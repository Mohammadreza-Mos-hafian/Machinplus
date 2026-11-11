from affiliate_module.models import ProviderLink
from travel.models import Hotel, Tour, FlightTicket
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import F, FloatField, ExpressionWrapper
from django.db.models.functions import Coalesce


def search_across_models(user_input):
    keywords = user_input.lower().split()

    hotel_query = Q()
    tour_query = Q()
    flight_query = Q()

    for word in keywords:
        hotel_query |= Q(keywords__icontains=word)
        tour_query |= Q(keywords__icontains=word)
        flight_query |= Q(keywords__icontains=word)

    # search
    hotel_results = Hotel.objects.filter(hotel_query).distinct()
    tour_results = Tour.objects.filter(tour_query).distinct()
    flight_results = FlightTicket.objects.filter(flight_query).distinct()

    def serialize(queryset, fields):
        return [
            {field: getattr(obj, field, None) for field in fields}
            for obj in queryset
        ]

    hotels_data = serialize(hotel_results, ['id', 'title'])
    tours_data = serialize(tour_results, ['id', 'title'])
    flights_data = serialize(flight_results, ['id', 'origin', 'destination'])

    result = {
        "hotels": hotels_data,
        "tours": tours_data,
        "flights": flights_data,
    }

    return result


def find_best_providers_by_ai_keywords(ai_keywords_list, min_rank=0.01):
    search_terms = " ".join(ai_keywords_list).split()

    q_objects = Q()
    for term in search_terms:
        q_objects |= Q(label__icontains=term)
        q_objects |= Q(description__icontains=term)
        q_objects |= Q(manual_keywords__icontains=term)

    results = ProviderLink.objects.filter(q_objects).order_by('price')

    formatted_services = []
    for link in results:
        formatted_services.append({
            "title": link.label,
            "price": link.price,
            "link": link.link,
            "image": link.image.url,
            "provider": link.provider.title,
            "currency": link.currency,
            "desc": link.description[:100] + "..." if hasattr(link, 'description') else ""
        })

    return formatted_services[:5]
