# Function extracted_with_Gemini
# Input: resume text, job description
# Output: current skills, key strengths, missing skills, areas for improvement

import json
import requests
import argparse
import os
import sys
import re

# Trước khi in ra, thay đổi thiết lập mã hóa đầu ra của Python
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = ''
url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}'

def extracted_with_Gemini(resume_text, job_description):
    prompt = f"""
        You are an expert resume analyst with deep knowledge of industry standards, job requirements, and hiring practices across various fields. Your task is to provide a comprehensive, detailed analysis of the resume provided.

        Please structure your response in the following format:

        ## Current Skills
        - **Current Skills**: [List ALL skills the candidate demonstrates in their resume, categorized by type (technical, soft, domain-specific, etc.). Be comprehensive.]

        ## Key Strengths
        [List 5-7 specific strengths of the resume with detailed explanations of why these are effective]

        Additionally, compare this resume to the following job description:

        Job Description:

        {job_description}

        ## Missing Skills
        [List specific requirements from the job description that are not addressed in the resume, with recommendations on how to address each gap]

        ## Areas for Improvement
        [List 5-7 specific areas where the resume could be improved with detailed, actionable recommendations]

        Resume:

        {resume_text}
        """

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Gửi yêu cầu POST
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses

        # Lấy nội dung kết quả từ API
        result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        sections = re.split(r'##\s+', result)
        sections = [s.strip() for s in sections if s.strip()]
        section_dict = {}

        for section in sections:
            lines = section.splitlines()
            title = lines[0].strip().lower().replace(" ", "_")  #"Current Skills" → "current_skills"
            content = "\n".join(lines[1:]).strip()
            section_dict[title] = content

        current_skills = section_dict.get("current_skills", "")
        key_strengths = section_dict.get("key_strengths", "")
        missing_skills = section_dict.get("missing_skills", "")
        areas_for_improvement = section_dict.get("areas_for_improvement", "")

        return current_skills, key_strengths, missing_skills, areas_for_improvement
        
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")

if __name__ == "__main__":
    cv = """
    Mick Dreeling
 Director - Games Data Science and Engineering
 San Francisco Bay Area
 Summary
 Managing engineering for game data tech at Netflix.
 Previously Engineering Manager for the Streaming Data Engineering
 team at Netflix. Working with a talented team of Engineers to curate,
 process and present information on the Playback Experience
 for Netflix customers. This data is one of the most important and
 critical datasets at the company, and requires us to deliver the best
 possible information to our internal stakeholders on how customers
 are interacting with our content, leading to an improved Netflix
 experience for everyone!
 Professional Experience
 ==================
 Java,Hive, Presto, Spark, Hadoop, Tableau
 iOS, Android, Unity
 Amazon, GCP
 Self Interest
 ==================
 Data Science : Self learning and Berkeley
 iOS Development : Used to build iOS Apps back in 2009/2010
 FPGA development : Soldered together an OSSC from scratch using
 off the shelf components
 https://junkerhq.net/xrgb/index.php/OSSC
 Electronics : Like to fix broken Guitar Effects and video game
 consoles such as Neo-Geo's
 Cars : Like working on old cars and engines
 Blockchain : I wrote a crypto coin dedicated to my dog from scratch,
 cloning LiteCoin and integrating Dark Gravity Wave retargeting.
 Experience
 Netflix
 Page 1 of 5
  
6 years 2 months
 Director - Games Data Science and Engineering
 January 2025 - Present (3 months)
 San Francisco Bay Area
 Cross functional role leading a talented group of Data Science, Analytics and
 Data Engineering teams for Games at Netflix. 
These teams work on both portfolio and studio level projects helping games at
 Netflix reach new heights.
 Director - Game Data Engineering and Analytics Engineering
 December 2021 - February 2025 (3 years 3 months)
 San Francisco Bay Area
 Leading a team to develop game analytics at Netflix. This includes all Analytics
 Engineering and Dashboards, as well as integration with iOS and Android
 SDK's in Objective-C and Java, real-time pipeline development in Flink/Scala
 and delivery of metrics to various dashboards, UI's and algorithms. 
Engineering Manager - Streaming Video Data
 February 2019 - December 2021 (2 years 11 months)
 San Francisco Bay Area
 Engineering Lead for Streaming Video Data Engineering at Netflix. 
My team owns the datasets that answer the following questions:
 * What is being watched on Netflix?
 * Which devices are watching Netflix and are they experiencing problems?
 * What is the quality of the member experience in both the Player and the
 App?
 This data is one of the most important and critical datasets at the company,
 and requires us to deliver the best possible information to our internal
 stakeholders on how customers are interacting with our content, leading to an
 improved Netflix experience for everyone!
 Riot Games
 5 years 8 months
 Head of Data Engineering
 January 2015 - January 2019 (4 years 1 month)
 Santa Monica
 Page 2 of 5
  
I led Riot's Data Engineering group to about 35-40 people at any one point in
 time, during staggering growth of League of Legends, and deployed smaller
 embedded teams into the R&D phases of Valorant and others. This included
 ownership of both the platform side (Kafka, ElasticSearch, EMR, Vertica,
 Tableau) and the data modelling and warehousing side (Telemetry creation,
 and Fact and dimension tables for the games). 
It was an exciting journey that I was really proud to be a part of.
 Helped Riot to...
 * Administer and curate one of gaming's largest Data-Warehouse's using
 Hadoop, Hive and Vertica
 * Deliver Analytics Tools for the entire company to use
 * Build and Maintain Systems in Java to Ingest over 30 billion events per day
 and not break a sweat
 * Assist customers in the use of our Self-Service Data Pipeline and help them
 to decide what data to collect
 * Make League of Legends better, and keep players happy!
 Engineering Manager - Big Data
 June 2013 - December 2014 (1 year 7 months)
 Los Angeles, California, United States
 Sun Life Financial
 9 years 2 months
 Applications Development Associate Director
 July 2012 - June 2013 (1 year)
 Wellesley, MA
 Technical Lead and Resource Manager for J2EE projects using REST
 webservices and ExtJS
 Applications Development Senior Manager
 February 2010 - July 2012 (2 years 6 months)
 Wellesley, MA
 Technical Lead and Resource Manager for projects using J2EE with Flex and
 ExtJS.
 Senior Software Engineer (Applications Development Analyst)
 October 2008 - February 2010 (1 year 5 months)
 Same role as previously but now working in US Office in Wellesley, MA
 Page 3 of 5
  
Senior Software Engineer
 May 2004 - October 2008 (4 years 6 months)
 Java Engineer with Weblogic/Flex at Waterford Office, Ireland. Worked
 primarily on the automated workflow system for Sunlife
 Bolands Waterford
 Software Engineer / IT Manager
 May 2003 - May 2004 (1 year 1 month)
 General IT Management and writing custom PHP/Java applications for
 Automotive Group
 James F. Wallace & Co. Chartered Accountants
 Software Engineer / IT Manager
 May 2002 - May 2003 (1 year 1 month)
 General IT Management and writing PHP/Java applications for Accountancy
 Firm
 Marconi PLC
 Software Design Engineer
 September 2000 - May 2002 (1 year 9 months)
 County Dublin, Ireland
 Java Engineer in Telecommuniations. Wrote software to parse data records
 coming from Marconi network equipment.
 Celtech Software Group
 Systems Administrator
 1999 - 2000 (1 year)
 Systems administrator for network on Windows NT4. Also coded Installshield
 scripts for development team.
 Education
 University of California, Berkeley
 Masters Degree, Data Science/AI · (August 2022 - January 2025)
 Waterford Institute of Technology
 Master's Degree, Computer Science · (2014)
 Waterford Institute of Technology
 Bachelor of Science in Applied Computing, Computer Science · (2000)
    """

    jd = """
    Your key responsibilities:

    The Fresher Software Developer will be responsible for developing and maintaining applications using a low-code development platform, setting up and configuring systems for each customer's unique requirements. 
    If you are naturally drawn to technology and understanding it, and if you are looking for an opportunity in a fast-paced software development environment where you can develop your technical skills and soft skills in parallel, then you might be a match

Qualifications

General requirements:

    Good IT background, GPA 7.5+ (Please attach transcripts when submitting your CV)
    Problem-solving skills and solution-oriented attitude
    Ability to work independently and in a team setting
    Good English skills
    Ready to work full-time

Technical requirements:

    Having experience with one programming language (C#, .NET, Java, Python) and a drive to learn and work with C#
    Theoretical knowledge of softwar'e development good practices and basic software design patterns
    """


    current_skills, key_strengths, missing_skills, areas_for_improvement = extracted_with_Gemini(cv, jd)


    print("\ncurrent_skills: \n", current_skills)
    print("\nkey_strengths: \n", key_strengths)
    print("\nmissing_skills: \n", missing_skills)
    print("\nareas_for_improvement: \n", areas_for_improvement)