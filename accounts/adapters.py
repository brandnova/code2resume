from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Auto-populates user profile fields from social provider data
    when a user signs up or connects a social account.
    """

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        data = sociallogin.account.extra_data

        provider = sociallogin.account.provider

        if provider == 'google':
            if not user.avatar_url:
                user.avatar_url = data.get('picture', '')
            if not user.display_name:
                user.display_name = data.get('name', '')

        elif provider == 'github':
            if not user.avatar_url:
                user.avatar_url = data.get('avatar_url', '')
            if not user.display_name:
                user.display_name = data.get('name', '') or data.get('login', '')
            if not user.github_username:
                user.github_username = data.get('login', '')
            if not user.website:
                user.website = data.get('blog', '')
            if not user.bio:
                user.bio = data.get('bio', '') or ''

        user.save()
        return user