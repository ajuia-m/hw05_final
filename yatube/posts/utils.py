from django.core.paginator import Paginator

POST_COUNT_PER_PAGE = 10


def func_paginator(request, posts):
    paginator = Paginator(posts, POST_COUNT_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
