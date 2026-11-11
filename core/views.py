import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from blog.models import Magazine
from core.models import ChatMessage, InquiryForm
from shop.models import Product
from utils.gpt import gpt_request


# Create your views here.
def home(request):
    products = Product.objects.filter(is_active=True)[:3]
    articles = Magazine.objects.filter(status="published")[:3]

    context = {
        "products": products,
        "articles": articles
    }
    return render(request, 'core/home.html', context=context)


@csrf_exempt
def inquiry_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            InquiryForm.objects.create(
                full_name=data.get('full_name', ''),
                phone_number=data.get('phone_number', ''),
                q1=data.get('q1', ''),
                q2=data.get('q2', ''),
                q3=data.get('q3', ''),
                q4=data.get('q4', ''),
                q5=data.get('q5', ''),
                q6=data.get('q6', ''),
                q7=data.get('q7', ''),
                q8=data.get('q8', ''),
                q9=data.get('q9', ''),
                q10=data.get('q10', ''),
                q11=data.get('q11', ''),
                q12=data.get('q12', ''),
                status='read'
            )
            return JsonResponse({'status': 'success', 'message': 'پرسشنامه با موفقیت ثبت شد.'}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'خطا در ثبت اطلاعات', 'details': str(e)}, status=400)

    return render(request, 'core/inquiry_form.html')


def contact_view(request):
    return render(request, 'core/contact.html')


def terms(request):
    return render(request, 'core/terms.html')


@csrf_exempt
def chatbot_view(request):
    if request.method == "POST":

        try:
            # user prompt
            data = json.loads(request.body)
            user_lang = data.get("lang_code", "")
            user_message = data.get("message", "")
            client_history = data.get("history", [])
            if not user_message:
                return JsonResponse({"error": "Message is required"}, status=400)

            # gpt request for client
            # gpt_response = gpt_request(user_lang, client_history, user_message, request.user.id)
            gpt_response = gpt_request(user_prompt=user_message, client_history=client_history)
            # save user prompt and gpt response
            # chat_message = ChatMessage(
            #     user_message=user_message,
            #     bot_message=gpt_response
            # )
            # if request.user.is_authenticated:
            #     chat_message.user = request.user
            # chat_message.save()

            # results = find_best_providers_by_ai_keywords(gpt_response[1])

            return JsonResponse(
                {
                    "reply": gpt_response[0],
                    # "results": results
                },
                status=200
            )

        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, status=500)

    messages = None
    if request.user.is_authenticated:
        messages = ChatMessage.objects.filter(user=request.user)
    context = {
        "messages": messages
    }
    return render(request, 'core/chatbot.html', context=context)
