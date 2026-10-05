import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_sweden_country_and_catalog_are_consistent():
    countries = json.loads((ROOT / "data" / "countries.json").read_text(encoding="utf-8"))
    assert countries["se"]["timezone"] == "Europe/Stockholm"
    assert countries["se"]["sources"] == ["https://www.open-epg.com/files/sweden1.xml.gz"]
    assert countries["se"]["catalog"] == "channels_se.json"

    catalog = json.loads((ROOT / "data" / "channels_se.json").read_text(encoding="utf-8"))
    channels = catalog["channels"]
    assert len(channels) == 16
    assert [channel["order"] for channel in channels] == list(range(1, 17))
    assert len({channel["id"] for channel in channels}) == 16

    ids = {xmltv_id for channel in channels for xmltv_id in channel["xmltv_ids"]}
    for required in {"SVT1.se", "SVT2.se", "TV4.se", "Kanal5.se", "Sjuan.se", "SVT24.se", "Kunskapskanalen.se"}:
        assert required in ids

def test_sweden_is_enabled_in_addon_schema():
    config = (ROOT / "config.yaml").read_text(encoding="utf-8")
    assert 'country: "list(de|at|ch|nl|be|no|fr|se)"' in config
