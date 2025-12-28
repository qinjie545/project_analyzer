def test_health(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_pull_config_save_and_get(client):
    payload = {
        'sources': ['GitHub'],
        'keywords': 'ai, data',
        'rule': 'best_match',
        'frequency': 'weekly',
        'weekday': 1,
        'timesPerWeek': 2,
        'startTime': '09:30',
        'concurrency': 5,
        'perProjectDelay': 1,
        'batch': 50
    }
    r = client.post('/api/pull/config', json=payload)
    assert r.status_code == 200
    assert r.get_json()['success'] is True

    r2 = client.get('/api/pull/config')
    assert r2.status_code == 200
    data = r2.get_json()['data']
    assert data['rule'] == 'best_match'
    # server should echo keywords string and also expose parsed keywords_list
    assert 'keywords' in data
    assert data['keywords'] == payload['keywords']
    assert 'keywords_list' in data and isinstance(data['keywords_list'], list)


def test_make_enqueue_and_logs(client):
    r = client.post('/api/make/enqueue', json={'task_id': 'task_test_001'})
    assert r.status_code == 200
    assert r.get_json()['success'] is True
    r2 = client.get('/api/make/logs/task_test_001')
    assert r2.status_code == 200
    assert r2.get_json()['success'] is True
    r3 = client.get('/api/make/tasks')
    assert r3.status_code == 200
    assert r3.get_json()['success'] is True


def test_publish_history(client):
    payload = {'title': 'Weekly Digest', 'platform': '微信公众号', 'url': 'https://example.com/post/1'}
    r = client.post('/api/publish/test', json=payload)
    assert r.status_code == 200
    assert r.get_json()['success'] is True
    r2 = client.get('/api/publish/history')
    assert r2.status_code == 200
    data = r2.get_json()['data']
    assert isinstance(data, list)


def test_publish_config(client):
    r3 = client.post('/api/publish/config', json={'platforms':['微信公众号'],'account':'gh-weekly','apiKey':'secret','publishTime':'09:00'})
    assert r3.status_code == 200 and r3.get_json()['success']
    r4 = client.get('/api/publish/config')
    assert r4.status_code == 200 and r4.get_json()['success']


def test_pull_test_and_records(client):
    payload = {'rule': 'best_match', 'keywords': 'ai, data', 'task_id': 'pull_task_001'}
    r = client.post('/api/pull/test', json=payload)
    assert r.status_code == 200
    assert r.get_json()['success'] is True
    r2 = client.get('/api/pull/records')
    assert r2.status_code == 200
    data = r2.get_json()['data']
    assert isinstance(data, list)
    if len(data):
        assert 'octocat/Hello-World' in data[0]['name']

