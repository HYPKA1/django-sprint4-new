from django.core.paginator import Paginator

from .constants import POSTS_LIMIT


def paginate_posts(request, posts):
    """Пагинация постов."""
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
