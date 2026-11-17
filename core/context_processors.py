def seo_defaults(request):
    return {
        "seo_title": "ماشین پلاس | راهکار جامع تامین و نوسازی ماشین آلات",
        "seo_description": "ماشین پلاس، راهکار جامع تامین و نوسازی ماشین آلات صنعتی با امکان خرید اعتباری.",
        "seo_type": "website",
        "seo_url": request.build_absolute_uri(request.path),
        "seo_image": "",
    }
