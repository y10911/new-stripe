from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

# Use a test secret key from Stripe for demo purposes
stripe.api_key = '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'

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    return response

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.get_json()
    service_name = data.get('serviceName')
    quantity = data.get('quantity')
    subtotal = data.get('subtotal')
    purchase_type = data.get('purchaseType')
    min_order = data.get('minOrder')
    unit_type = data.get('unitType')
    base_price = data.get('basePrice')  # Get base price
    additional_fee = data.get('additionalFee', 0)  # Additional fee if any

    print(f"Received values: service_name={service_name}, quantity={quantity}, subtotal={subtotal}, purchase_type={purchase_type}, min_order={min_order}, unit_type={unit_type}, base_price={base_price}, additional_fee={additional_fee}")

    try:
        if purchase_type == "one-time":
            # Create a Stripe Checkout session for one-time purchase
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': service_name,
                            },
                            'unit_amount': int(round(subtotal * 100)),  # Convert to cents
                        },
                        'quantity': quantity,
                    }
                ],
                mode='payment',
                success_url="https://www.designteam.co/success",
                cancel_url=data['cancel_url'],
                allow_promotion_codes=True,  # Allow promotion codes
                client_reference_id=service_name  # Pass the service name as client reference
            )
        elif purchase_type == "subscription":
            # Calculate additional units
            additional_units = quantity - min_order

            # Append additional fee line item if applicable
            line_items = [
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': service_name,
                        },
                        'unit_amount': int(round(base_price * 100)),  # Convert to cents
                    },
                    'quantity': min_order,
                }
            ]

            if additional_units > 0:
                line_items.append(
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"{service_name} Additional Fee",
                                'description': f"{additional_units} additional {unit_type}",
                            },
                            'unit_amount': int(round(additional_fee * 100)),  # Convert to cents
                        },
                        'quantity': 1,
                    }
                )

            # Create a Stripe Checkout session for subscription
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='subscription',
                success_url="https://www.designteam.co/membership-success",
                cancel_url=data['cancel_url'],
                allow_promotion_codes=True,  # Allow promotion codes
                client_reference_id=service_name  # Pass the service name as client reference
            )
        else:
            return jsonify(error="Invalid purchase type"), 400

        return jsonify(session_id=session.id), 200

    except stripe.error.StripeError as e:
        # Handle Stripe API errors
        return jsonify(error=str(e)), 400
    except Exception as e:
        # Handle other errors
        return jsonify(error="An error occurred while creating the session"), 500

if __name__ == '__main__':
    app.run(debug=True)