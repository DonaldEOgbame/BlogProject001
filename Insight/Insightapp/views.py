# Django built-in imports
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
# from django.db.models import Count
# from django.core.paginator import Paginator
from .forms import CustomUserCreationForm, CustomAuthenticationForm, PostForm, CommentForm
from .models import Post, Comment, Reaction, UserFollowing, CustomUser, ReadingHistory, ReadLater, UpvotedPost, UserPreference
from .utility import get_for_you_articles, get_recommended_authors, get_recommended_posts


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Redirect to a success page.
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_request(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                # Invalid login - handle error
                pass
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_request(request):
    logout(request)
    return redirect('home')


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # For saving ManyToMany relations like tags
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def update_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)  # Ensuring the user is the author of the post
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == 'POST':
        post.delete()
        return HttpResponseRedirect(reverse('blog_home'))  # Redirect to the blog home
    return render(request, 'blog/post_confirm_delete.html', {'post': post})


@login_required
@require_POST
def toggle_reaction(request):
    user = request.user
    model_type = request.POST.get('model_type')  # 'post' or 'comment'
    object_id = request.POST.get('object_id')
    reaction_type = request.POST.get('reaction_type')

    model = Post if model_type == 'post' else Comment
    content_type = ContentType.objects.get_for_model(model)

    try:
        reaction = Reaction.objects.get(
            content_type=content_type,
            object_id=object_id,
            user=user
        )
        # Toggle or remove the reaction
        if reaction.reaction_type == reaction_type:
            reaction.delete()
            reaction_type = None
        else:
            reaction.reaction_type = reaction_type
            reaction.save()
    except Reaction.DoesNotExist:
        # Create a new reaction
        Reaction.objects.create(
            content_type=content_type,
            object_id=object_id,
            user=user,
            reaction_type=reaction_type
        )

    return JsonResponse({'success': True, 'reaction_type': reaction_type})


@login_required
def user_reactions(request):
    # Assuming Article is the model to which reactions are made
    article_content_type = ContentType.objects.get_for_model(Post)

    # Fetch reactions made to articles
    article_reactions = Reaction.objects.filter(
        user=request.user,
        content_type=article_content_type
    ).select_related('content_object')

    return render(request, 'user_reactions.html', {'article_reactions': article_reactions})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.filter(parent__isnull=True)  # Top-level comments

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.author = request.user
            # If it's a reply to another comment
            parent_id = request.POST.get('parent_id')
            if parent_id:
                new_comment.parent_id = int(parent_id)
            new_comment.save()
            return redirect(post)
    else:
        comment_form = CommentForm()

    if request.user.is_authenticated:
        current_preferences = UserPreference.objects.get(user=request.user)
        current_preferences.preferred_tags.add(*post.tags.all())
        current_preferences.save()

    return render(request, 'blog/post_detail.html', {'post': post, 'comments': comments, 'comment_form': comment_form})


@login_required
def update_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)  # Ensure only the author can edit
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('post_detail', pk=post_id)  # Redirect back to the post
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/edit_comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)  # Ensure only the author can delete
    if request.method == 'POST':
        comment.delete()
        return redirect('post_detail', pk=post_id)  # Redirect back to the post
    return render(request, 'blog/delete_comment_confirm.html', {'comment': comment})


def for_you(request):
    articles = get_for_you_articles(request.user) if request.user.is_authenticated else Post.objects.all()
    return render(request, 'for_you.html', {'articles': articles})


@login_required
def follow_user(request, username):
    # Prevent users from following themselves
    if request.user.username == username:
        return HttpResponseForbidden()

    target_user = get_object_or_404(CustomUser, username=username)
    # Create the following relationship if it doesn't exist
    UserFollowing.objects.get_or_create(user=request.user, following_user=target_user)
    return HttpResponseRedirect('/profile/' + username)


@login_required
def unfollow_user(request, username):
    # Prevent users from unfollowing themselves
    if request.user.username == username:
        return HttpResponseForbidden()

    target_user = get_object_or_404(CustomUser, username=username)
    # Delete the following relationship if it exists
    UserFollowing.objects.filter(user=request.user, following_user=target_user).delete()
    return HttpResponseRedirect('/profile/' + username)


def following(request):
    if request.user.is_authenticated:
        # Get the list of users that the current user is following
        following_users = UserFollowing.objects.filter(user=request.user).values_list('following_user', flat=True)

        # Fetch articles from the followed users
        articles = Post.objects.filter(author_id__in=following_users).order_by('-created_at')[:20]  # Adjust limit as needed
    else:
        articles = []

    return render(request, 'following.html', {'articles': articles})


@login_required
def reading_history(request):
    history = ReadingHistory.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'reading_history.html', {'history': history})


@login_required
def user_posts(request):
    posts = Post.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'user_posts.html', {'posts': posts})


@login_required
def comment_history(request):
    comments = Comment.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'comment_history.html', {'comments': comments})


@login_required
def add_to_read_later(request, article_id):
    article = get_object_or_404(Post, pk=article_id)
    ReadLater.objects.get_or_create(user=request.user, article=article)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def remove_from_read_later(request, article_id):
    ReadLater.objects.filter(user=request.user, article_id=article_id).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def read_later_list(request):
    articles = ReadLater.objects.filter(user=request.user).order_by('-added_on')
    return render(request, 'read_later_list.html', {'articles': articles})


def recommended_authors_view(request):
    if request.user.is_authenticated:
        authors = get_recommended_authors(request.user)
    else:
        authors = CustomUser.objects.none()

    return render(request, 'recommended_authors.html', {'authors': authors})


def recommended_posts_view(request):
    if request.user.is_authenticated:
        posts = get_recommended_posts(request.user)
    else:
        posts = Post.objects.none()

    return render(request, 'recommended_posts.html', {'posts': posts})
