def test_pull_run_simulate(client):
    payload = { 'keyword': 'GPT', 'limit': 1, 'simulate': True }
    r = client.post('/api/pull/run', json=payload)
    assert r.status_code == 200
    data = r.get_json()['data']
    assert data['count'] == 1
