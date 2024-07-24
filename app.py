from flask import Flask, jsonify, request
import stripe
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use a test secret key from Stripe for demo purposes
stripe.api_key = 'sk_test_51Of6goKZ0oo6AUWAhVAGBbJgiaBVpVUkPLBQOdVE4RKnE38lsscMVc85p2j0s6EjAD0bBOxz4pUIAh13t3UwWiTe00kHiko9gx'

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', 'https://try-design-team.webflow.io/')
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    return response

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.get_json()
    service_name = data.get('serviceName')
    quantity = data.get('quantity')
    subtotal = data.get('subtotal')
    
    try:
        # Create a Stripe Checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': service_name,
                        },
                        'unit_amount': subtotal // quantity,
                    },
                    'quantity': quantity,
                }
            ],
            mode='payment',
            success_url=data['success_url'],
            cancel_url=data['cancel_url'],
        )
        logging.info(f"Session created: {session.id}")
        return jsonify({'id': session.id})
    except Exception as e:
        logging.error(f"Error creating session: {e}")
        return jsonify(error=str(e)), 403

if __name__ == '__main__':
    app.run(port=4242)
