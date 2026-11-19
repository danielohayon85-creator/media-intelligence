def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_demo_seed_and_dashboard_flow(client):
    seed_resp = client.post("/api/demo/seed")
    assert seed_resp.status_code == 200
    data = seed_resp.json()
    org_id = data["organization_id"]
    assert data["items_new"] > 0

    items_resp = client.get(f"/api/items?organization_id={org_id}&page_size=5")
    assert items_resp.status_code == 200
    items_data = items_resp.json()
    assert items_data["total"] > 0
    assert len(items_data["items"]) <= 5
    for item in items_data["items"]:
        assert item["analysis"] is not None
        assert item["analysis"]["relevance"] != "not_relevant"

    kpis_resp = client.get(f"/api/dashboard/kpis?organization_id={org_id}")
    assert kpis_resp.status_code == 200
    kpis = kpis_resp.json()
    assert kpis["total_mentions"] >= items_data["total"]

    trend_resp = client.get(f"/api/dashboard/trend?organization_id={org_id}")
    assert trend_resp.status_code == 200
    assert trend_resp.json()["granularity"] == "daily"

    quality_resp = client.get(f"/api/dashboard/data-quality?organization_id={org_id}")
    assert quality_resp.status_code == 200
    assert quality_resp.json()["items_pending_analysis"] == 0


def test_manual_correction_is_recorded(client):
    seed_resp = client.post("/api/demo/seed")
    org_id = seed_resp.json()["organization_id"]
    item_id = client.get(f"/api/items?organization_id={org_id}&page_size=1").json()["items"][0]["id"]

    patch_resp = client.patch(
        f"/api/items/{item_id}/analysis",
        json={"sentiment": "neutral", "correction_notes": "תיקון בדיקה"},
    )
    assert patch_resp.status_code == 200
    analysis = patch_resp.json()["analysis"]
    assert analysis["sentiment"] == "neutral"
    assert analysis["manually_corrected"] is True
    assert analysis["correction_notes"] == "תיקון בדיקה"
