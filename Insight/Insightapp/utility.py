from django.db.models import Count, Q
from .models import Post, UpvotedPost, UserPreference, UserFollowing, CustomUser, Reaction



def get_for_you_articles(user):
    following_users = UserFollowing.objects.filter(user=user).values_list('following_user_id', flat=True)
    upvoted_articles = UpvotedPost.objects.filter(user=user).values_list('article_id', flat=True)
    preferred_tags = UserPreference.objects.get(user=user).preferred_tags.all()

    articles = Post.objects.filter(
        Q(author__id__in=following_users) |
        Q(id__in=upvoted_articles) |
        Q(tags__in=preferred_tags)
    ).distinct().order_by('-created')[:20]  # Ensure 'created' is the correct field name

    return articles


def get_recommended_authors(user):
    user_preferences = UserPreference.objects.get(user=user)
    user_interests = user_preferences.preferred_tags.all()

    authors_with_similar_interests = CustomUser.objects.filter(
        post__main_tag__in=user_interests  # Assuming a user has posts linked via a 'post' related name
    ).distinct()

    # Assuming CustomUser has a field 'post' related to Post, and Post has a 'likes' or similar mechanism
    trending_authors = CustomUser.objects.annotate(
        num_likes=Count('post__likes')  # Adjust 'likes' field as per your model
    ).order_by('-num_likes')[:10]

    recommended_authors = set(list(authors_with_similar_interests) + list(trending_authors))
    return recommended_authors


def get_recommended_posts(user):
    user_preferences = UserPreference.objects.get(user=user)
    user_interests = user_preferences.preferred_tags.all()
    upvoted_posts = Reaction.objects.filter(user=user, reaction_type=Reaction.UPVOTE).values_list('object_id', flat=True)

    user_activity_posts = Post.objects.filter(
        Q(main_tag__in=user_interests) |
        Q(subtag__in=user_interests) |
        Q(id__in=upvoted_posts)
    ).distinct()

    # Combining and deduplicating post lists
    recommended_posts = set(list(user_activity_posts))
    return recommended_posts


