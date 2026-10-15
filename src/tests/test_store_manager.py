"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
from store_manager import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    # 1. Créez un article (`POST /products`)
    product_data = {'name': 'Some Item', 'sku': '12345', 'price': 99.90}
    response = client.post('/products',
                          data=json.dumps(product_data),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['product_id'] > 0 
    response_stock = client.post('/stocks', data=json.dumps({'product_id': data['product_id'], 'quantity': 5}), content_type='application/json')
    assert response_stock.status_code == 201
    # 2. Ajoutez 5 unités au stock de cet article (`POST /stocks`)
    response_stock = client.get(f'/stocks/{data["product_id"]}')
    assert response_stock.status_code == 200
    assert response_stock.get_json()['quantity'] == 5
    # 3. Vérifiez le stock, votre article devra avoir 5 unités dans le stock (`GET /stocks/:id`)
    response_order = client.post('/orders', data=json.dumps({'user_id': 1, 'items': [{'product_id': data['product_id'], 'quantity': 2}]}), content_type='application/json')
    assert response_order.status_code == 201
    # 4. Faites une commande de l'article que vous avez crée, 2 unités (`POST /orders`)
    response_stock_after_order = client.get(f'/stocks/{data["product_id"]}')
    assert response_stock_after_order.status_code == 200
    assert response_stock_after_order.get_json()['quantity'] == 3
    # 5. Vérifiez le stock encore une fois (`GET /stocks/:id`)
    response_delete_order = client.delete(f'/orders/{response_order.get_json()["order_id"]}')
    assert response_delete_order.status_code == 200
    response_stock_after_delete = client.get(f'/stocks/{data["product_id"]}')
    assert response_stock_after_delete.status_code == 200
    assert response_stock_after_delete.get_json()['quantity'] == 5
    # 6. Étape extra: supprimez la commande et vérifiez le stock de nouveau. Le stock devrait augmenter après la suppression de la commande.
