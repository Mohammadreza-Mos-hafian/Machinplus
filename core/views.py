import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST

from blog.models import Magazine
from cart.views import get_cart_summary
from core.models import ChatMessage, InquiryForm
from shop.models import Product
from utils.gpt import gpt_request
from utils.functions import get_year, get_user_cart

from core.image_processing import get_responsive_image_data


def home(request):
    products = Product.objects.filter(is_active=True)[:3]
    articles = Magazine.objects.filter(status="published")[:3]

    for product in products:
        product.image_data = get_responsive_image_data(
            product.main_image
        )

    for article in articles:
        article.image_data = get_responsive_image_data(
            article.cover_image
        )

    context = {
        "products": products,
        "articles": articles,
        "year": get_year()
    }

    return render(request, "core/home.html", context)


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

    context = {
        "year": get_year()
    }

    return render(request, 'core/inquiry_form.html', context=context)


def contact_view(request):
    context = {
        "year": get_year(),
        "cart_items_count": get_cart_summary(get_user_cart(request))["items_count"],
    }

    return render(request, 'core/contact.html', context=context)


def terms(request):
    context = {
        "year": get_year(),
        "cart_items_count": get_cart_summary(get_user_cart(request))["items_count"],
    }

    return render(request, 'core/terms.html', context=context)


@require_POST
@csrf_protect
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
            return JsonResponse({"error": str(e)}, status=503)

    messages = None
    if request.user.is_authenticated:
        messages = ChatMessage.objects.filter(user=request.user)
    context = {
        "messages": messages,
    }
    return render(request, 'core/chatbot.html', context=context)


def catalog_view(request):
    return render(request, "core/catalog.html")


def custom_404(request, exception):
    return render(
        request,
        "404.html",
        status=404,
        context={
            "page_title": "صفحه پیدا نشد",
            "cart_items_count": get_cart_summary(get_user_cart(request))["items_count"],
        },
    )


def custom_500(request):
    return render(
        request,
        "500.html",
        status=500,
        context={
            "page_title": "خطای داخلی سرور",
            "cart_items_count": get_cart_summary(get_user_cart(request))["items_count"],
        },
    )


def robots_txt(request):
    content = """User-agent: *
Disallow: /management-panel/
Disallow: /cart/
Disallow: /ckeditor/

Sitemap: https://machinplus.ir/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")
