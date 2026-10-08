from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AccountForm, CommentForm

from .models import Comment, Post, Tag

# Create your views here.

def index(request):
    sort_options = {
        'newest': ('-created_at',),
        'oldest': ('created_at',),
        'most_comments': ('-comment_count', '-created_at'),
        'fewest_comments': ('comment_count', '-created_at'),
    }
    selected_sort = request.GET.get('sort', 'newest')
    if selected_sort not in sort_options:
        selected_sort = 'newest'

    posts = Post.objects.prefetch_related('tags')
    if selected_sort in ('most_comments', 'fewest_comments'):
        posts = posts.annotate(comment_count=Count('comments'))

    posts = posts.order_by(*sort_options[selected_sort])
    selected_tag = request.GET.get('tag')
    if selected_tag:
        posts = posts.filter(tags__slug=selected_tag)

    return render(request, 'blog/index.html', {
        'posts': posts,
        'tags': Tag.objects.all(),
        'selected_tag': selected_tag,
        'selected_sort': selected_sort,
    })


def account(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            return redirect('blog:index')
        return render(request, 'blog/account.html', {'form': AccountForm()})

    form = AccountForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        User = get_user_model()
        username_field = User.USERNAME_FIELD
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(
            request,
            **{username_field: username, 'password': password},
        )

        if user is not None:
            login(request, user)
            messages.success(request, 'Sesión iniciada correctamente.')
            return redirect('blog:account')

        user_exists = User._default_manager.filter(
            **{username_field: username}
        ).exists()
        if user_exists:
            form.add_error('password', 'El nombre de usuario o la contraseña no son correctos.')
        else:
            new_user = User(**{username_field: username})
            try:
                validate_password(password, user=new_user)
            except ValidationError as error:
                form.add_error('password', error)
            else:
                user = User._default_manager.create_user(
                    **{username_field: username, 'password': password}
                )
                login(request, user)
                messages.success(request, 'Cuenta creada y sesión iniciada correctamente.')
                return redirect('blog:account')

    return render(request, 'blog/account.html', {'form': form})


@require_POST
@login_required(login_url='blog:account')
def logout_view(request):
    logout(request)
    messages.success(request, 'Cerramos tu sesión correctamente.')
    return redirect('blog:logged_out')


def logged_out(request):
    return render(request, 'blog/logged_out.html')


def detail(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.name = request.user.get_username() if request.user.is_authenticated else 'Anónimo'
            comment.save()

            return redirect('blog:detail', slug=slug)
    else:
        form = CommentForm()

    return render(request, 'blog/detail.html', {
        'post' : post,
        'form': form
    })


@require_POST
def delete_comment(request, slug, comment_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    comment = get_object_or_404(Comment, pk=comment_id, post__slug=slug)
    comment.delete()
    return redirect('blog:detail', slug=slug)
