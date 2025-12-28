def test_pull_run_by_config_simulate(client):
    # ensure a config exists by posting one via API
    client.post('/api/pull/config', json={'keywords':'GPT,AI','rule':'most_stars','batch':1})
    r = client.post('/api/pull/run/config', json={'simulate': True})
    assert r.status_code == 200
    data = r.get_json()['data']
    assert data['count'] >= 1
    # keywords from config should be parsed and used
    assert isinstance(data['keywords'], list)
    assert 'GPT' in data['keywords'] and 'AI' in data['keywords']


def test_pull_run_by_config_override_keywords(client):
    # base config in DB
    client.post('/api/pull/config', json={'keywords':'GPT,AI','rule':'most_stars','batch':1})
    # override keywords via request payload
    r = client.post('/api/pull/run/config', json={'simulate': True, 'keywords': 'vue3'})
    assert r.status_code == 200
    data = r.get_json()['data']
    assert data['count'] >= 1
    assert isinstance(data['keywords'], list)
    assert 'vue3' in data['keywords']
    # old config keywords should not be used when override is provided
    assert 'GPT' not in data['keywords'] and 'AI' not in data['keywords']
