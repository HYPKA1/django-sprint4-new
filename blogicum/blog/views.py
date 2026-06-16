from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .paginations import paginate_posts

from .forms import CommentForm, PostForm, UserEditForm
from .models import Category, Comment, Post


User = get_user_model()


def get_published_posts():
    """Опубликованные посты."""
    return Post.objects.select_related(
        'category',
        'location',
        'author',
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now(),
    ).annotate(
        comment_count=Count('comments')
    ).order_by(
        '-pub_date'
    )


def index(request):
    """Главная страница."""
    page_obj = paginate_posts(request, get_published_posts())
    context = {
        'page_obj': page_obj,
        'post_list': page_obj,
    }
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    """Страница отдельного поста."""
    post = get_object_or_404(
        Post.objects.select_related(
            'category',
            'location',
            'author',
        ).annotate(
            comment_count=Count('comments')
        ),
        pk=post_id
    )

    post_is_hidden = (
        not post.is_published
        or not post.category.is_published
        or post.pub_date > timezone.now()
    )

    if post_is_hidden and post.author != request.user:
        raise Http404('Публикация не найдена.')

    context = {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.select_related('author'),
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    """Посты по категориям."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = get_published_posts().filter(category=category)
    page_obj = paginate_posts(request, posts)
    context = {
        'category': category,
        'page_obj': page_obj,
        'post_list': page_obj,
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    """Страница пользователя."""
    profile = get_object_or_404(User, username=username)

    posts = Post.objects.select_related(
        'category',
        'location',
        'author',
    ).filter(
        author=profile
    ).annotate(
        comment_count=Count('comments')
    ).order_by(
        '-pub_date'
    )

    if request.user != profile:
        posts = posts.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        )

    page_obj = paginate_posts(request, posts)

    context = {
        'profile': profile,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    """Редактирование профиля."""
    form = UserEditForm(
        request.POST or None,
        instance=request.user,
    )

    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)

    context = {
        'form': form,
    }
    return render(request, 'blog/user.html', context)


@login_required
def create_post(request):
    """Создание публикации."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    """Редактирование публикации."""
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    context = {
        'form': form,
    }
    return render(request, 'blog/create.html', context)


@login_required
def delete_post(request, post_id):
    """Удаление публикации."""
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    form = PostForm(instance=post)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    context = {
        'post': post,
        'form': form,
    }
    return render(request, 'blog/create.html', context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    post = get_object_or_404(
        get_published_posts(),
        pk=post_id
    )
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария."""
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=post_id,
    )

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    form = CommentForm(request.POST or None, instance=comment)

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    context = {
        'form': form,
        'comment': comment,
    }
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария."""
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=post_id,
    )

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    context = {
        'comment': comment,
    }
    return render(request, 'blog/comment.html', context)


def registration(request):
    """Регистрация пользователя."""
    form = UserCreationForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('login')

    context = {
        'form': form,
    }
    return render(request, 'registration/registration_form.html', context)
