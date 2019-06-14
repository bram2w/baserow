def test_homepage(client):
    response = client.get('/api/')
    assert response.json()['detail'] == 'Authentication credentials were not provided.'
    assert response.status_code == 401
