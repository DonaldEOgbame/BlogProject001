from django.contrib.auth.models import AbstractUser
from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.conf import settings


class CustomUser(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics', null=True, blank=True)
    email = models.EmailField('email address', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class MainTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SubTag(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # User who created the subtag

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = RichTextField()
    published_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    featured_image = models.ImageField(upload_to='posts/%Y/%m/%d/', blank=True, null=True)
    main_tag = models.ForeignKey(MainTag, on_delete=models.CASCADE)
    subtag = models.ForeignKey(SubTag, on_delete=models.SET_NULL, null=True, blank=True)
    comments_count = models.IntegerField(default=0)
    excerpt = models.TextField(null=True, blank=True)
    view_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class Reaction(models.Model):
    UPVOTE = 'upvote'
    DOWNVOTE = 'downvote'

    REACTION_CHOICES = [
        (UPVOTE, 'Upvote'),
        (DOWNVOTE, 'Downvote'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=8, choices=REACTION_CHOICES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ['user', 'content_type', 'object_id', 'reaction_type']

    def __str__(self):
        return f"{self.user} - {self.reaction_type}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    content = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    @property
    def is_reply(self):
        return self.parent is not None


class UserFollowing(models.Model):
    user = models.ForeignKey(CustomUser, related_name="following", on_delete=models.CASCADE)
    following_user = models.ForeignKey(CustomUser, related_name="followers", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'following_user')


class UpvotedPost(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    article = models.ForeignKey(Post, on_delete=models.CASCADE)
    upvoted_on = models.DateTimeField(auto_now_add=True)


class UserPreference(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='preferences')
    preferred_tags = models.ManyToManyField(MainTag)

    def update_preferences(self, new_tag_ids):
        """
        Update the preferred tags for the user.
        `new_tag_ids` should be a list of ids corresponding to MainTag instances.
        """
        new_tags = MainTag.objects.filter(id__in=new_tag_ids)
        self.preferred_tags.set(new_tags)
        self.save()


class ReadingHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    article = models.ForeignKey(Post, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)


class ReadLater(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='read_later')
    article = models.ForeignKey(Post, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'article')

    def __str__(self):
        return f"{self.article.title} (Read Later by {self.user.username})"
