from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

POSTS_CONST = 10


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, POSTS_CONST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'title': title,
        'posts': posts,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Страница со списком опубликовавнных постов."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POSTS_CONST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/group_list.html'
    title = 'Группы сообщества'
    context = {
        'title': title,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Здесь код запроса к модели и создание словаря контекста."""
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, POSTS_CONST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_count = posts.count()
    following = request.user.is_authenticated and (
        Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    )
    template = 'posts/profile.html'
    title = f'Профайл пользователя {username}'
    context = {
        'title': title,
        'page_obj': page_obj,
        'author': author,
        'posts': posts,
        'post_count': post_count,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    pub_date = post.pub_date
    post_count = author.posts.all().count()
    template = 'posts/post_detail.html'
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'author': author,
        'pub_date': pub_date,
        'post_count': post_count,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)
    return render(request, template, {'form': form, 'is_edit': True})


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
    paginator = Paginator(posts, POSTS_CONST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect(
            'posts:profile',
            username=username
        )
    follower = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if follower is True:
        return redirect(
            'posts:profile',
            username=username
        )
    Follow.objects.create(user=request.user, author=author)
    return redirect(
        'posts:profile',
        username=username
    )


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect(
            'posts:profile',
            username=username
        )
    following = get_object_or_404(Follow, user=request.user, author=author)
    following.delete()
    return redirect(
        'posts:profile',
        username=username
    )
