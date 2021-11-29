import re
import json
import requests
from requests.api import head, options
import streamlit as st
from nltk.util import everygrams
from copy import deepcopy
import urllib

class GitProfile:

    def __init__(self):
        st.set_page_config(
            page_title="GitHub Profile Generator",
            initial_sidebar_state="expanded",
            layout="wide",
            page_icon="https://raw.githubusercontent.com/github/explore/main/topics/github/github.png"
            )
        with open('metadata.json') as f:
            self.metadata = json.load(f)
    
    @st.cache(show_spinner=False, suppress_st_warning=True, allow_output_mutation=True)
    def is_valid_url(self, url):
        valid = True
        try:
            requests.get(url, timeout=5)
        except:
            valid = False
        return valid

    @st.cache(show_spinner=False, suppress_st_warning=True, allow_output_mutation=True)
    def load_git_topics(self):
        """
            Load GitHub Topics
        """
        # https://api.github.com/repos/gilbarbara/logos/git/trees/master?recursive=1
        topics = {}
        try:
            url = 'https://raw.githubusercontent.com/github/explore/main/topics'
            response = requests.get('https://github.com/github/explore/file-list/main/topics', timeout=5)
            topics = re.findall(r"\/topics\/(.*)\/(?:\1).png", response.text)
            topics = {i: f'{url}/{i}/{i}.png' for i in set(topics)}
        except Exception as e:
            st.error(e)
        return topics

    @st.cache(show_spinner=False, suppress_st_warning=True, allow_output_mutation=True)
    def get_user_info(self, username):
        """
            Get github user info
        """
        user_info = {}
        try:
            url = f'https://api.github.com/users/{username}'
            user_info = requests.get(url, timeout=5).json()
            if user_info and user_info.get('login'):
                user_info['languages'], user_info['repos'] = self.get_additional_user_info(username)
            else:
                raise 'User not found'
        except:
            user_info = {}
            st.error('Invalid username')
        return user_info
    
    @st.cache(show_spinner=False, suppress_st_warning=True, allow_output_mutation=True)
    def get_additional_user_info(self, username):
        """
            Get most used languages by user
        """
        languages, repos = [], []
        try:
            with st.spinner('Getting user details..'):
                url = f'https://api.github.com/users/{username}/repos'
                response = requests.get(url, timeout=5)
                for i in response.json():
                    if not i['fork']:
                        repos.append(i['name'])
                        lang_url = i['languages_url']
                        lang_resp = requests.get(lang_url, timeout=5)
                        languages.extend(lang_resp.json().keys())
        except Exception as e:
            st.error(e)
        languages = list(set(languages))
        return languages, repos
    
    def add_to_markdown(self, text):
        self.readme_markdown += text + '\n'
    
    def clear_markdown(self):
        self.readme_markdown = ''
    
    def make_st_changes(self):
        # Adjust sidebar width and padding
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
                width: 500px;
                height: 111vh;
                padding-top: 1.5rem;
            }
            [tabindex="0"] > div:first-child {
                padding-top: 0rem;
                padding-left: 3rem;
                padding-right: 3rem;
                padding-botton: 3rem;
            }
            [class="stTextArea"] > label:first-child {
                min-height: 0rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        # Hide mainmenu and footer
        st.markdown(
            """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            html {zoom: 90%}
            </style>
            """,
            unsafe_allow_html=True
        )
    
    def add_greeting(self, username):
        exp = st.sidebar.expander(label='Greeting')

        # Greeting/Heading
        if not self.user_info:
            greeting_default = ''
        elif self.user_info.get('name'):
            greeting_default = f'Hi there, I am {self.user_info["name"]} 👋'
        else:
            greeting_default = 'Hi there 👋'
        greeting = exp.text_input(
            label='Text',
            value=greeting_default
            )
        if greeting:
            self.add_to_markdown(f'### {greeting}\n')
        
        if exp.checkbox('Show Visitors Count?'):
            col1, col2, col3 = exp.columns([6,4,2])
            vc_label = col1.text_input('Label', value='Profile Views')
            vc_style = col2.selectbox('Style', options=['plastic', 'flat','flat-square'], index=0)
            vc_color = col3.color_picker('Color', value='#0969da')
            params = {
                'username': username,
                'label': vc_label,
                'style': vc_style,
                'color': vc_color.strip('#')
            }
            url_params = urllib.parse.urlencode(params)
            widget_url = f'https://komarev.com/ghpvc/?{url_params}'
            self.add_to_markdown(f'<p><img src="{widget_url}" alt="visitors_count"></p>\n')

    def add_about_me(self):
        exp = st.sidebar.expander(label='About me')
        header = exp.text_input(
            label='Heading',
        )
        about_me_points = [
            '- 🔭 I’m currently working on ...',
            '- 🌱 I’m currently learning ...',
            '- 👯 I’m looking to collaborate on ...',
            '- 🤔 I’m looking for help with ...',
            '- 💬 Ask me about ...',
            '- 📫 How to reach me: ...',
            '- 😄 Pronouns: ...',
            '- ⚡ Fun fact: ...'
            ]
        about_me = exp.text_area(
            label='Info',
            value='\n'.join(about_me_points) if self.user_info else '',
            height=230
        )
        if about_me:
            if header:
                self.add_to_markdown(f'\n**{header}**\n')
            self.add_to_markdown(about_me)

    def add_contacts(self):
        exp = st.sidebar.expander(label='Contacts')
        col1, col2 = exp.columns([3,2])
        header = col1.text_input(
            label='Heading',
            value='Connect with me:'
        )
        icon_type = col2.radio(
            label='Icon type',
            options=['color', 'black & white']
        )
        warning_placeholder = exp.empty()
        if icon_type == 'black & white':
            url = 'https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons'
        else:
            url = 'https://raw.githubusercontent.com/shashankdeshpande/github-profile-generator/main/logos'

        sites = ['LinkedIn','Twitter', 'Instagram','YouTube','Medium','StackOverflow']
        n_cols = 2
        site_chunks = [sites[i:i + n_cols] for i in range(0, len(sites), n_cols)]
        contacts = {}
        for i in site_chunks:
            col1, col2 = exp.columns(n_cols)
            input_data = {
                i[0].lower(): col1.text_input(i[0]),
                i[1].lower(): col2.text_input(i[1])
            }
            for k, v in input_data.items():
                if v and self.is_valid_url(v):
                    contacts[k] = v
                elif v:
                    warning_placeholder.error(f'Invalid URL for {k}!\n\nEnter URL starting with http/https')

        if contacts:
            icon_size = exp.number_input(
                    label='Icon Size',
                    value=30,
                    key='contact'
                )
            if header:
                self.add_to_markdown(f'\n**{header}**\n')

            contact_markdown = ''
            for key, val in contacts.items():
                if val:
                    icon_data = f'<code style="background: transparent;"><a href="{val}" target="_blank"><img src="{url}/{key}.svg" height="{icon_size}" /></a></code>'
                    contact_markdown += icon_data
            self.add_to_markdown(contact_markdown)
    
    def add_technology_stack(self):
        # Language and tools
        exp = st.sidebar.expander(label='Technology Stack')
        topics = self.load_git_topics()
        header = exp.text_input(
            label='Heading',
            value='Technology Stack'
        )

        user_keywords = deepcopy(self.user_info.get('languages',[]))
        if self.user_info.get('bio'):
            bio = re.sub(r'[^a-zA-Z0-9]', ' ', self.user_info['bio'])
            ngrams = map(lambda x: ' '.join(x), everygrams(bio.split()))
            user_keywords.extend(ngrams)
            user_keywords = list(map(lambda x: x.strip().lower(), user_keywords))
        user_keywords = list(map(lambda x: x.strip().lower(), user_keywords))

        common_tools = set(topics.keys()).intersection(user_keywords)
        tools = exp.multiselect(
            label='Tools',
            options=topics.keys(),
            default=common_tools if common_tools else None
        )
        icon_size = 30
        if tools and header:
            self.add_to_markdown(f'\n**{header}**\n')
            icon_size = exp.number_input(
                label='Icon Size',
                value=icon_size
            )
        for i in tools:
            self.add_to_markdown(f'<code><img height="{icon_size}" src="{topics[i]}"></code>')
        
    def show_copy_button(self):
        from bokeh.models.widgets import Button
        from bokeh.models import CustomJS
        from streamlit_bokeh_events import streamlit_bokeh_events
        copy_button = Button(
            label="Copy to clipboard",
            width=30,
            height=32,
            margin=(0,0,0,0),
            sizing_mode ='fixed'
            )
        copy_button.js_on_event("button_click", CustomJS(args=dict(text=self.readme_markdown), code="""
            navigator.clipboard.writeText(text);
            """))

        no_event = streamlit_bokeh_events(
            copy_button,
            events="GET_TEXT",
            key="get_text",
            refresh_on_update=True,
            override_height=40,
            debounce_time=0)
    
    def add_git_stats(self, username):
        exp = st.sidebar.expander(label='GitHub Stats (Add-ons)')
        git_stats_dict = {}
        two_col_size = [1,14]
        three_col_size = [1,7,7]
        lang_exists = self.user_info.get('languages',[])
        
        if lang_exists and exp.checkbox('Show Top Languages?'):
            compact_layout = exp.columns(two_col_size)[1].checkbox('compact layout?')
            trisplit = exp.columns(three_col_size)
            langs_count = trisplit[1].number_input('languages count', 1, 10, 5)
            hide = trisplit[2].multiselect('hide languages', options=self.user_info['languages'])
            trisplit = exp.columns(three_col_size)
            exclude_repo = trisplit[1].multiselect('exclude repositories', options=self.user_info['repos'])
            theme = trisplit[2].selectbox('theme', options=self.metadata['stats_card_themes'], index=0, key='top_lang')
            params = {
                'username': username,
                'layout': 'compact' if compact_layout else '',
                'langs_count': langs_count,
                'hide': ','.join(hide),
                'exclude_repo': ','.join(exclude_repo),
                'theme': theme
            }
            url_params = urllib.parse.urlencode(params)
            widget_url = f'https://github-readme-stats.vercel.app/api/top-langs?{url_params}'
            git_stats_dict['top_langs'] = widget_url
            exp.markdown("""----""")

        if exp.checkbox('Show Stats Card?'):
            custom_title = exp.columns(two_col_size)[1].text_input('title', f"{self.user_info['name']}'s GitHub Stats" if self.user_info.get('name') else '')
            trisplit = exp.columns(three_col_size)
            show_icons = trisplit[1].checkbox('show icons?', value=True)
            count_private = trisplit[2].checkbox('count private?')

            trisplit = exp.columns(three_col_size)
            hide_rank = trisplit[1].checkbox('hide rank?')
            include_all_commits = trisplit[2].checkbox('include all commits?')

            trisplit = exp.columns(three_col_size)
            hide = trisplit[1].multiselect('hide', options=['stars','commits','prs','issues','contribs'])
            theme = trisplit[2].selectbox('theme', options=self.metadata['stats_card_themes'], index=0)

            params = {
                'username': username,
                'show_icons': str(show_icons).lower(),
                'count_private': str(count_private).lower(),
                'hide_rank': str(hide_rank).lower(),
                'include_all_commits': str(include_all_commits).lower(),
                'theme': theme,
                'custom_title': custom_title,
                'hide_title': 'true' if not custom_title else 'false',
                'hide': ','.join(hide),
            }
            url_params = urllib.parse.urlencode(params)
            widget_url = f'https://github-readme-stats.vercel.app/api?{url_params}'
            git_stats_dict['stats_card'] = widget_url
            exp.markdown("""----""")

        if exp.checkbox('Show Streak Stats?'):
            trisplit = exp.columns(three_col_size)
            hide_border = exp.columns(two_col_size)[1].checkbox('hide border?')
            theme = exp.columns(two_col_size)[1].selectbox('theme', options=self.metadata['stats_card_themes'], index=0, key='streak')
            params = {
                'user': username,
                'theme': theme,
                'hide_border': str(hide_border).lower()
            }
            url_params = urllib.parse.urlencode(params)
            widget_url = f'https://github-readme-streak-stats.herokuapp.com/?{url_params}'
            git_stats_dict['streak'] = widget_url
            exp.markdown("""----""")
        
        if exp.checkbox('Show Trophy?'):
            trisplit = exp.columns(three_col_size)
            no_bg = trisplit[1].checkbox('no background?')
            no_frame = trisplit[2].checkbox('no frame?')

            trisplit = exp.columns(three_col_size)
            rank = trisplit[1].multiselect('exclude rank', options=self.metadata['trophy_ranks'])
            rank = set(self.metadata['trophy_ranks'])-set(rank)
            theme = trisplit[2].selectbox('theme', options=self.metadata['trophy_themes'], index=0, key='trophy')

            trisplit = exp.columns(three_col_size)
            row = trisplit[1].number_input('max rows', min_value=1, value=3)
            column = trisplit[2].number_input('max columns', min_value=1, value=6)

            trisplit = exp.columns(three_col_size)
            margin_w = trisplit[2].number_input('margin width', min_value=0, value=0, step=2)
            margin_h = trisplit[1].number_input('margin height', min_value=0, value=0, step=2)

            params = {
                'username': username,
                'no-bg': str(no_bg).lower(),
                'no-frame': str(no_frame).lower(),
                'rank': ','.join(rank),
                'theme': theme,
                'row': row,
                'column': column,
                'margin-w': margin_w,
                'margin-h': margin_h
            }
            url_params = urllib.parse.urlencode(params)
            widget_url = f'https://github-profile-trophy.vercel.app/?{url_params}'
            git_stats_dict['trophy'] = widget_url
        
        if git_stats_dict:
            self.add_to_markdown('\n**GitHub Stats**\n')
            for k,v in git_stats_dict.items():
                self.add_to_markdown(f'<p><img src="{v}" alt="{k}"></p>')
            
        
    def main(self):
        self.make_st_changes()
        self.clear_markdown()
        main_header = '''
            <a href="https://github.com/shashankdeshpande/github-profile-generator" target="_blank" style="text-decoration: none; color: black">
                <p style="font-size: larger;">
                    <code style="background: transparent; padding-top=1rem">
                    <img src="https://raw.githubusercontent.com/github/explore/main/topics/github/github.png" height="30" />
                    </code>
                GitHub Profile Generator
                </p>
            </a>'''
        st.sidebar.write(main_header, unsafe_allow_html=True)

        col1, _, col2, col3 = st.columns([10,0.4, 2.8,2.3])
        col1.markdown('Repository: https://github.com/shashankdeshpande/github-profile-generator', unsafe_allow_html=True)

        profile_place = st.empty()

        username = st.sidebar.text_input(
            label='GitHub Username'
            )
        if username:
            self.user_info = self.get_user_info(username)
        else:
            self.user_info = {}
            st.warning('Please enter GitHub Username from left menu to continue.')

        self.add_greeting(username)
        self.add_about_me()
        self.add_contacts()
        self.add_technology_stack()
        if self.user_info:
            self.add_git_stats(username)

        if self.readme_markdown:
            with st.expander('README file preview'):
                self.readme_markdown = st.text_area('', value=self.readme_markdown, height=500)
            
            with col2:
                self.show_copy_button()
            col3.download_button(
                label="📥 README",
                data=self.readme_markdown,
                file_name="README.md",
            )
            
            with profile_place.expander('Profile preview', expanded=True):
                st.write(self.readme_markdown, unsafe_allow_html=True)
        st.sidebar.info('Developed by [Shashank Deshpande](https://www.linkedin.com/in/shashank-deshpande)')
        
if __name__ == "__main__":
    obj = GitProfile()
    obj.main()