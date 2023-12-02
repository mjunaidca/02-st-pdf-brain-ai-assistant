## Project Challenge: Build AI Agents with OpenAI's Assistant API - Quick Streamlit Tutorial

I have developed and prototyped the complete concept in chat_witj_pdf.ipynb file. 

We have a Class that Manages are assistant operations. 

## Assistant And Files Creation

- We first retrive and check if the assistant already exists before creating a new assistant. 

###### *Problem Addressed*: Rather than createing a new assistant or file we first check if the same file already exists

#### Know Problems and Possible Solutions in this Mental Modal:

1. Two Different users upload same a pdf file with same name ??? 
- POSSIBLE SOLUTION: DESTRY FILES AFTER USER SESSION COMPLETION AND REMOVE THE EXISTING CHECK.

2, We have 200 Assistants in the list. 
- We can brainstorm from the following:
    1. Hard Code the Assistant ID - We create assistant in playground and then use that ID to modify it only. 
    2. Create a new assistant and destry it

    In this approach My Plan is to keepo current implementation and destry the assistant as well.

    No need to keep assistant and files in the backend. Create an assistant - use it and destry it. Or keep the assistant - detach the files else delete the files as well.

-> Ultimatily It will depend on the concept that we are building - this base concept is the seed idea that I plan to use in future projects.

Feel free to raise the PR, create issues and share your thoughts on how can we improve it.

A Few Good References:

https://github.com/theailifestyle/AssistantsAPI/tree/main

https://www.youtube.com/watch?v=TCYgN6R0-RU

https://ec.ai/why-a-reasoning-engine-can-solve-your-problems/

https://community.openai.com/t/questions-about-assistant-threads/485239/3

https://github.com/langroid/langroid/blob/main/langroid/agent/openai_assistant.py

