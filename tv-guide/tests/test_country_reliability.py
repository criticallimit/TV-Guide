"""Verified broadcaster schedules and incomplete country feeds must stay distinct."""
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("reliability_app", Path(__file__).parents[1] / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app = app.backend


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        patches = patch.multiple(app, OPTIONS_FILE=root / "options.json", CACHE_FILE=root / "feed.xml.gz",
                                 PARSED_CACHE_FILE=root / "parsed.json", CHANNEL_PREFS_FILE=root / "order.json")
        patches.start()
        self.addCleanup(patches.stop)

    def test_npo_resolves_station_from_public_catalogue_and_preserves_exact_times(self):
        store = app.EPGStore("nl")
        provider = app.COUNTRIES["nl"]["providers"]["nl_npo1"]
        today = datetime.now(app.EPG_TIMEZONE).replace(hour=8, minute=0, second=0, microsecond=0)
        def fetch(url, label):
            if url == provider["channels_url"]:
                return json.dumps([{"title": "NPO2", "guid": "wrong"}, {"title": "NPO1", "guid": "correct"}])
            self.assertIn("guid=correct", url)
            day = datetime.strptime(url.split("date=")[1].split("&")[0], "%d-%m-%Y").date()
            start = today.replace(year=day.year, month=day.month, day=day.day)
            return json.dumps([{"mainTitle": "Live", "programStart": int(start.timestamp()),
                                "programEnd": int((start + timedelta(hours=8, seconds=17)).timestamp())},
                               {"mainTitle": "Stale", "programStart": int((start - timedelta(days=6)).timestamp()),
                                "programEnd": int((start - timedelta(days=6, hours=-1)).timestamp())}])
        with patch.object(store, "_fetch_html", side_effect=fetch):
            rows = store._fetch_official_programs("nl_npo1", provider)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["title"] == "Live" for row in rows))
        self.assertTrue(all(datetime.fromisoformat(row["end"]) - datetime.fromisoformat(row["start"])
                            == timedelta(hours=8, seconds=17) for row in rows))

    def test_vtm_rejects_other_stations_stale_dates_and_missing_timezones(self):
        store = app.EPGStore("be")
        day = datetime.now(app.EPG_TIMEZONE).date().isoformat()
        def event(title, station="VTM GOLD", start=None):
            return {"@type": "BroadcastEvent", "name": title, "publishedOn": {"name": station},
                    "startDate": start or day + "T12:00:00Z", "endDate": day + "T20:00:00Z"}
        values = [event("Valid"), event("Other station", "VTM"), event("No timezone", start=day + "T12:00:00"),
                  event("Stale", start="2000-01-01T12:00:00Z")]
        page = '<script type="application/ld+json">' + json.dumps(values) + '</script>'
        with patch.object(store, "_fetch_html", return_value=page):
            rows = store._fetch_official_programs("be_vtmgold", app.COUNTRIES["be"]["providers"]["be_vtmgold"])
        self.assertEqual([row["title"] for row in rows], ["Valid"])
        self.assertEqual(datetime.fromisoformat(rows[0]["end"]) - datetime.fromisoformat(rows[0]["start"]), timedelta(hours=8))
        start = datetime.fromisoformat(rows[0]["start"])
        self.assertEqual(start.utcoffset(), start.astimezone(app.EPG_TIMEZONE).utcoffset())

    def test_vrt_paginates_and_keeps_midnight_on_following_date(self):
        store = app.EPGStore("be")
        provider = app.COUNTRIES["be"]["providers"]["be_vrt1"]
        day = datetime.now(app.EPG_TIMEZONE).date()
        page_id = f"/vrtmax/tv-gids/vrt1/{day}/"
        def node(title, time):
            return {"title": title, "indexMeta": [{"value": time}], "statusMeta": [{"value": "30 min"}]}
        def response(query):
            paged = "after:" in query
            items = [node("After midnight", "00:15u")] if paged else [node("Evening", "23:50u")]
            return {"data": {"page": {"id": page_id, "brand": "een", "previous": {},
                                     "next": {"paginatedItems": {"edges": [{"node": n} for n in items],
                                              "pageInfo": {"hasNextPage": not paged, "endCursor": "second"}}}}}}
        with patch.object(store, "_fetch_public_schedule_json", side_effect=lambda url, query: response(query)) as fetch:
            rows = store._fetch_vrt_programmes(provider, day)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual([row["title"] for row in rows], ["Evening", "After midnight"])
        self.assertEqual(rows[1]["start_dt"].date(), day + timedelta(days=1))
        self.assertEqual(rows[0]["end_dt"], rows[1]["start_dt"])

    def test_vrt_rejects_wrong_station_and_date(self):
        store = app.EPGStore("be")
        provider = app.COUNTRIES["be"]["providers"]["be_vrt1"]
        day = datetime.now(app.EPG_TIMEZONE).date()
        for page in [{"id": f"/vrtmax/tv-gids/vrt1/{day}/", "brand": "canvas"},
                     {"id": "/vrtmax/tv-gids/vrt1/2000-01-01/", "brand": "een"}]:
            with patch.object(store, "_fetch_public_schedule_json", return_value={"data": {"page": page}}):
                self.assertEqual(store._fetch_vrt_programmes(provider, day), [])

    def test_vrt_repeated_cursor_cannot_loop_or_silently_accept_partial_schedule(self):
        store = app.EPGStore("be")
        day = datetime.now(app.EPG_TIMEZONE).date()
        page = {"id": f"/vrtmax/tv-gids/vrt1/{day}/", "brand": "een",
                "next": {"paginatedItems": {"edges": [], "pageInfo": {"hasNextPage": True, "endCursor": "same"}}}}
        with patch.object(store, "_fetch_public_schedule_json", return_value={"data": {"page": page}}):
            with self.assertRaises(ValueError):
                store._fetch_vrt_programmes(app.COUNTRIES["be"]["providers"]["be_vrt1"], day)

    def test_complete_veronica_variant_cannot_be_claimed_by_partial_name_match(self):
        store = app.EPGStore("nl")
        source = store.cache_file.with_suffix(".xml")
        source.write_text('<tv><channel id="Veronica.nl"><display-name>Veronica</display-name></channel>'
                          '<channel id="VeronicaDisneyJr..nl"><display-name>Veronica / Disney Jr.</display-name></channel></tv>')
        with patch.object(store, "_open_xml", side_effect=lambda: source.open("rb")):
            mapping = store._build_channel_map()
        self.assertEqual(mapping["nl_veronica"]["xmltv_id"], "VeronicaDisneyJr..nl")
        self.assertEqual(len({v["xmltv_id"] for v in mapping.values()}), 2)

    def test_coverage_uses_actual_intervals_not_available_flags_or_feed_horizon(self):
        store = app.EPGStore("be")
        now = datetime.now(app.EPG_TIMEZONE).replace(hour=12, minute=0, second=0, microsecond=0)
        store.channels = [{"id": "complete", "preset": True, "available": True,
                           "programs": [{"start": (now - timedelta(hours=1)).isoformat(),
                                         "end": (now + timedelta(hours=10)).isoformat()}]},
                          {"id": "expired", "preset": True, "available": True,
                           "programs": [{"start": (now - timedelta(days=2)).isoformat(),
                                         "end": (now - timedelta(days=1)).isoformat()}]},
                          {"id": "future", "preset": True, "available": True,
                           "programs": [{"start": (now + timedelta(days=1)).isoformat(),
                                         "end": (now + timedelta(days=1, hours=10)).isoformat()}]}]
        metrics = store.coverage_metrics(now)
        self.assertEqual(metrics["current_channels"], 1)
        self.assertEqual(metrics["missing_current_channels"], ["expired", "future"])
        self.assertEqual(metrics["days"][0]["channels_with_evening_programmes"], 1)
        self.assertEqual(metrics["days"][1]["missing_evening_channels"], ["complete", "expired"])

    def test_shared_public_schedules_do_not_replace_regional_private_variants(self):
        for country, ids in [("at", ["at_rtl", "at_vox"]),
                             ("ch", ["ch_rtl", "ch_vox", "ch_sat1", "ch_artefr"])]:
            for channel_id in ids:
                self.assertNotIn(channel_id, app.COUNTRIES[country]["providers"])
        for channel_id, marker in {"at_sat1": "sat1-at", "at_prosieben": "prosieben-at",
                                   "at_kabeleins": "kabeleins-at", "at_sixx": "sixx-at"}.items():
            provider = app.COUNTRIES["at"]["providers"][channel_id]
            self.assertEqual(provider["kind"], "joynat")
            self.assertEqual(provider["marker"], marker)


if __name__ == "__main__":
    unittest.main()
