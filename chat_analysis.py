# Importing the needed libraries;

import re
import regex
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import emoji
import seaborn as sns
import plotly.express as px
from collections import Counter
#import wordcloud
#from wordcloud import WordCloud, STOPWORDS


#setting default app layout
st.set_page_config(
    page_title='Bwhiz chat analysis App',
    layout='wide'   
)

#To hide the menu icon
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


st.title('<\Bwhiz> WhatsApp Chat Analysis')


#---------------------------------------------------------#
# defining the regex for extracting datetime, author and message;

#defining a regex for extracting date and time info:
def date_and_time(entry):
    pattern = '^\d{1,2}/\d{1,2}/\d{1,2}, \d{1,2}:\d{1,2}\S [AaPp][Mm] -'
    result = re.match(pattern, entry)
    if result:
        return True
    return False

#defining a regex for extracting name of sender of messages:
def get_author(entry):
    patterns = [
        '([\w]+):',                        
        '([\w]+[\s]+[\w]+):',              
        '([\w]+[\s]+[\w]+[\s]+[\w]+):',    
        '([\w]+)[\u263a-\U0001f999]+:',               
    ]
    pattern = '^' + '|'.join(patterns)
    result = re.match(pattern, entry)
    if result:
        return True
    return False

#defining a regex for extracting datetime, the name of the sender of a message, and the message:
def get_data(entry):   
    splitentry = entry.split(' - ') 
    dateTime = splitentry[0]
    message = ' '.join(splitentry[1:])
    if get_author(message): 
        splitMessage = message.split(': ') 
        author = splitMessage[0] 
        message = ' '.join(splitMessage[1:])
    else:
        author = None
    return dateTime, author, message

col1, col2, col3= st.columns([1,0.0625,2])

with col1:
    # ------------------------------------------------------------------------------------- #
    chat_file = st.file_uploader(label="Please upload your file: ")
    if chat_file :

        #file handling and conversion to dataframe
        parsedData = []
        
        #conversationPath = chat_file  #replace with file upload
        # with open(conversationPath.name, encoding="utf-8") as fp:
        #     fp.readline() 
        messageBuffer = [] 
        datetime, author = None, None
        # while True:
        for line in chat_file:
            if not line: 
                break
            line = line.decode('UTF-8') 
            line = line.strip() 
            if date_and_time(line): 
                if len(messageBuffer) > 0: 
                    parsedData.append([dateTime, author, ' '.join(messageBuffer)]) 
                messageBuffer.clear() 
                dateTime, author, message = get_data(line) 
                messageBuffer.append(message) 
            else:
                messageBuffer.append(line)
    
        chat = pd.DataFrame(parsedData, columns=['DateTime', 'Author', 'Message']) 


        #Carrying out further cleaning on the generated dataframe:
        for i,j in enumerate(chat['Author']):
            if j is None:
                if len(chat['Message'][i].split(': ')) > 1:
                    chat['Author'][i] = chat['Message'][i].split(': ')[0]
                    chat['Message'][i] = chat['Message'][i].replace(chat['Message'][i].split(': ')[0],'').replace(':','')

                    
        #Converting the 'DateTime' column to pandas datetime object:
        chat['DateTime'] = pd.to_datetime(chat['DateTime'])

        # Carrying out some basic Feature Engineering :
        # ------------------------------------------------------------------------------------------------ #
        chat['Day'] = chat['DateTime'].apply(lambda x: x.day_name())            #to get the day the message was sent
        chat['month_sent'] = chat['DateTime'].apply(lambda x: x.month_name())   #to get the month the message was sent
        chat['date'] = [d.date() for d in chat['DateTime']]                     #to extract date from the DateTime object
        chat['hour'] = [d.time().hour for d in chat['DateTime']]                #to extract the hour of the day the message was sent
        
        #function to create emojis column;

        def split_count(text):
            emoji_list = []
            data = regex.findall(r'\X', text)
            for word in data:
                if any(char in emoji.UNICODE_EMOJI for char in word):
                    emoji_list.append(word)
            return emoji_list

        chat['emoji'] = chat['Message'].apply(split_count)
        # Null values in the Author column corresponds to Notifications , so I'd drop it:
        chat.dropna(axis=0, inplace=True)
        chat.drop(chat[chat['Message'] ==' <Media omitted>'].index, inplace=True) #dropping such values for the wordcloud not to give false results


    def convert_df(df):
        return df.to_csv().encode('utf-8')

    form = st.form(key='my_form')

    submit = form.form_submit_button(label='click here to get your chat dataframe')


    if submit:

        st.header("Output")

        st.write(chat)


        csv = convert_df(chat)

        st.download_button(
            label = "Download this output as CSV",
            data = csv,
            mime = 'text/csv'
        )


        if chat_file is not None:

            with col3:
                st.header('Visuals')
                fig = plt.figure(figsize=(12,8))
                plt.subplot(2,2,1)
                sns.barplot(x=chat['Author'].value_counts()[:10], y=chat['Author'].value_counts()[:10].keys())
                plt.title('Top 10 active members in the group my messages sent');

                plt.subplot(2,2,2)
                active_day = chat['Day'].value_counts()
                sns.barplot(x=active_day.keys(), y=active_day.values)
                plt.title('Most Active days')
                plt.xlabel('Days')
                plt.ylabel('No. of messages')
                plt.xticks(rotation=90);

                plt.subplots_adjust(wspace=0.4, hspace= 0.5)
                '''wordcloud = WordCloud(stopwords=STOPWORDS, background_color='white').generate(text)
                plt.figure(figsize=(12,8))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')'''
                st.pyplot(fig);



                emoji_list = list([a for b in chat.emoji for a in b])
                emoji_dict = dict(Counter(emoji_list))
                emoji_dict = sorted(emoji_dict.items(), key = lambda x: x[1], reverse=True)
                emoji_df = pd.DataFrame(emoji_dict, columns=['emoji','count'])

                fig = px.treemap(emoji_df, path=['emoji'],
                            values=emoji_df['count'].to_list(),title='Frequently Used Emojis')
                st.plotly_chart(fig, use_container_width=True)
