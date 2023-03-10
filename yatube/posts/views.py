from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import func_paginator

User = get_user_model()
POSTS_PAGE = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = func_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = func_paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj, }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user_selected = get_object_or_404(User,
                                      username=username)
    posts = Post.objects.filter(author__username=username)
    page_obj = func_paginator(request, posts)
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user).exists())
    context = {
        'page_obj': page_obj,
        'author': user_selected,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST,
                    files=request.FILES or None,
                    instance=post)
    context = {
        'form': form,
        'post': post,
        'is_edit': True}
    if request.method == "POST":
        if form.is_valid():
            post.save()
            return redirect('posts:post_detail', post_id)

    return render(request, 'posts/create_post.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
        )
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', new_post.author)
    else:
        form = PostForm()
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = func_paginator(request, posts)
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follow_author = get_object_or_404(User, username=username)

    if follow_author != request.user:
        Follow.objects.get_or_create(user=request.user, author=follow_author)

    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    follow_author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        author=follow_author, user=request.user).delete()

    return redirect('posts:profile', username)
