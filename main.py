import razorpay
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.requests import Request
from dotenv import load_dotenv
import json
import os


load_dotenv()


razorpay_client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')))


RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class Order(BaseModel):
    amount: int

@app.post("/create-order/")
async def create_order(order: Order):
    """Create an order with Razorpay for the given amount"""
    try:
        order_data = razorpay_client.order.create(dict(
            amount=order.amount * 100,  
            currency="INR",
            payment_capture="1"  #Auto capture payment after success
        ))
        json_str = json.dumps(order_data, indent=4)
        print(json_str)
        return JSONResponse(content={
            "order_id": order_data['id'],
            "currency": order_data['currency'],
            "amount": order_data['amount'],
            "order_data": order_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def get_payment_page(request: Request):
    razorpay_key_id = os.getenv('RAZORPAY_KEY_ID')  
    return templates.TemplateResponse("payment_page.html", {"request": request, "razorpay_key_id": razorpay_key_id})




class PaymentVerifyRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

@app.post("/verify-payment/")
def verify_payment(data: PaymentVerifyRequest):
    try:
       
        params_dict = {
            "razorpay_order_id": data.razorpay_order_id,
            "razorpay_payment_id": data.razorpay_payment_id,
            "razorpay_signature": data.razorpay_signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)


        payment_info = razorpay_client.payment.fetch(data.razorpay_payment_id)

        payment_str = json.dumps(payment_info,indent=4)
        print(payment_str)
        
        
        return {
            "status": "success",
            "payment_id": data.razorpay_payment_id,
            "amount": payment_info["amount"],
            "email": payment_info["email"],
            "contact": payment_info["contact"],
            "method": payment_info["method"],
            "created_at": payment_info["created_at"],
            "payment_info": payment_info 
        }

    except razorpay.errors.SignatureVerificationError:
        return {"status": "failed", "reason": "Invalid signature"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
# @app.get("/check-order")
# def check_order():
#     razorpay.Client
#     payments = razorpay_client.order.payments("order_QI69nW0FJ5CVHl")
#     payment_str = json.dumps(payments,indent=4)
#     print(payment_str)
#     return payment_str