import uuid
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model. Extends Django's AbstractUser so all default fields
    (email, first_name, last_name, password, is_active, etc.) are inherited.
    """
    display_name    = models.CharField(max_length=80,  blank=True)
    avatar_url      = models.URLField(max_length=500,  blank=True)
    bio             = models.TextField(max_length=300, blank=True)
    website         = models.URLField(max_length=300,  blank=True)

    def get_display_name(self):
        return self.display_name or self.first_name or self.email.split('@')[0]

    def __str__(self):
        return self.email
    

class Resume(models.Model):
    FRAMEWORK_CHOICES = [
        ('none',      'None'),
        ('tailwind',  'Tailwind CSS'),
        ('bootstrap', 'Bootstrap'),
    ]
    PAPER_CHOICES = [
        ('a4',     'A4'),
        ('letter', 'Letter'),
        ('legal',  'Legal'),
        ('a5',     'A5'),
    ]

    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title        = models.CharField(max_length=200, default='Untitled Resume')
    slug         = models.SlugField(max_length=220, unique=True, blank=True)
    html_content = models.TextField(blank=True)
    css_content  = models.TextField(blank=True)
    framework    = models.CharField(max_length=20, choices=FRAMEWORK_CHOICES, default='none')
    paper_size   = models.CharField(max_length=20, choices=PAPER_CHOICES,     default='a4')
    photo_url    = models.URLField(max_length=500, blank=True)
    is_public    = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base  = slugify(self.title)
            uid   = uuid.uuid4().hex[:8]
            self.slug = f"{base}-{uid}" if base else uid
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.user.email})"


class ResumeTemplate(models.Model):
    FRAMEWORK_CHOICES = [
        ('none',      'None'),
        ('tailwind',  'Tailwind CSS'),
        ('bootstrap', 'Bootstrap'),
    ]
    PAPER_CHOICES = [
        ('a4',     'A4'),
        ('letter', 'Letter'),
        ('legal',  'Legal'),
        ('a5',     'A5'),
    ]

    title        = models.CharField(max_length=200)
    slug         = models.SlugField(max_length=220, unique=True, blank=True)
    description  = models.TextField(blank=True)
    html_content = models.TextField()
    css_content  = models.TextField(blank=True)
    framework    = models.CharField(max_length=20, choices=FRAMEWORK_CHOICES, default='none')
    paper_size   = models.CharField(max_length=20, choices=PAPER_CHOICES,     default='a4')
    preview_image = models.ImageField(upload_to='template_previews/', blank=True)
    is_premium   = models.BooleanField(default=False)
    is_active    = models.BooleanField(default=True)
    order        = models.PositiveIntegerField(default=0, help_text="Display order on browse page")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            base = slugify(self.title)
            uid  = uuid.uuid4().hex[:6]
            self.slug = f"{base}-{uid}" if base else uid
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{'[Premium] ' if self.is_premium else ''}{self.title}"
    
