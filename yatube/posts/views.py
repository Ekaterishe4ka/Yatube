from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .models import Post, Group, User, Follow

from .forms import CommentForm, PostForm


COUNT_PUB: int = 10


def index(request):
    posts = Post.objects.select_related('author', 'group').all()
    paginator = Paginator(posts, COUNT_PUB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author').all()
    paginator = Paginator(posts, COUNT_PUB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author').all()
    paginator = Paginator(posts, COUNT_PUB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    is_following = (request.user.is_authenticated
                    and request.user != author
                    and Follow.objects.filter(
                        user=request.user,
                        author=author
                    ).exists())
    template = 'posts/profile.html'
    context = {
        'author': author,
        'page_obj': page_obj,
        'is_following': is_following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    post_count = author.posts.count()
    text = post.text
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'author': author,
        'post_count': post_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    if author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    form = PostForm(instance=post)
    context = {
        'form': form,
        'post_id': post_id,
        'post': post
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    username = request.user
    post = Post.objects.filter(author__following__user=username)
    paginator = Paginator(post, COUNT_PUB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if username != request.user.username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    follow = Follow.objects.filter(
        user=request.user,
        author__username=username
    )
    follow.delete()
    return redirect('posts:profile', username=username)
