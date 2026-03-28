
### Data Wrangling and Visualization — Group Coursework

## 1. Introduction

This report reflects on our experience developing the AI-Assisted Data Wrangler and Visualizer as part of our Data Wrangling and Visualization coursework. The project required us to build a fully functional, multi-page Streamlit web application that allows users to upload datasets, inspect and clean them, create visualizations, and export both the cleaned data and a record of all transformations applied. Working as a pair on a project of this size felt challenging at first, but it turned out to be one of the most useful things we have done in terms of actually putting what we have learned into practice.

## 2. How We Worked as a Team and Planned the Project

From the start, we tried to avoid just splitting things down the middle and working in total isolation. We had an initial meeting where we mapped out all the features the app needed and decided on a rough order to tackle them. We agreed early on that one of us would focus more on the data processing side — things like the file handler, the profiling functions, and the transformation logic — while the other concentrated on building out the Streamlit pages and making the interface feel usable and clear.

We used a shared folder to keep our files in sync and had regular check-ins to merge our work and test things together. This was important because we quickly found that things which seemed to work in isolation could break when connected to the rest of the app, especially anything involving session state. Having both of us look at problems together helped us debug a lot faster than either of us would have managed alone.

## 3. How We Developed the App

We built the app page by page, starting with the file upload and overview page before moving into cleaning and preparation, then visualization, and finally the export and report section. This order made sense to us because each later feature depended on earlier ones working properly. For example, the cleaning page could only be built properly once we had a reliable way of loading the data and storing it in session state.

We used modular helper files throughout to keep the page code readable. Functions for profiling the data, applying transformations, and building log entries were all kept in separate utility files and imported where needed. This made things much easier to test and debug, and it kept the Streamlit page files from becoming one enormous script that would have been really hard to follow.

## 4. What Was Difficult

The most consistently difficult part of the project was working with Streamlit's session state. Early on, we kept running into situations where a user would apply a transformation and navigate to another page, only for the data to reset completely. Understanding that Streamlit re-runs the entire script from top to bottom on every interaction took some getting used to, and it changed the way we thought about how to structure the app.

Connecting all the pages through a shared session state was also trickier than expected. We had to make sure that the same keys were initialised consistently on every page, because missing an initialisation call caused hard-to-trace errors. We eventually moved all the initialisation logic into a single utility function that we call at the top of every page, which helped a lot.

Deployment on Streamlit Cloud introduced its own set of problems. Several packages that worked fine on our local machines either behaved differently or were not available in the cloud environment, so we had to adjust our requirements file and test more carefully after every push. Time pressure in the final days made this particularly stressful, as small deployment bugs could eat up a lot of time that we had not budgeted for.

## 5. What Came More Naturally

Writing the individual transformation functions — things like filling missing values, removing duplicates, or scaling numeric columns — was actually one of the more straightforward parts of the project once we understood what each function needed to do. Pandas handles most of these operations cleanly, and keeping each function focused on a single task made them easy to write and test one by one.

The transformation logging system also came together without too much difficulty. Once we settled on a consistent dictionary format for each log entry, adding logging to new features was quick because we just followed the same pattern every time. Seeing the log build up as users applied changes felt like a good sign that the app was working as intended.

## 6. What We Learned Technically

This project gave us a much clearer understanding of what a real data wrangling workflow looks like. We had used pandas before, but mostly for individual tasks in isolation. Building an app where all the steps connect — load, inspect, clean, visualize, export — forced us to think about the full pipeline and how data quality decisions earlier on affect later stages.

We also learned a lot about writing safer code. Handling bad uploads gracefully, protecting against empty selections, checking whether a column exists before trying to transform it — these are the kinds of small defensive checks that we would have skipped before but now appreciate as essential for anything that real users will interact with. The importance of testing with messy, realistic data also became very clear, because a perfectly clean dataset can make bugs invisible.

## 7. What We Learned About Teamwork and Time Management

One thing that surprised us was how much time the integration phase took. Writing features individually went fairly quickly, but testing that they all worked together correctly, and fixing the bugs that appeared when they did not, took much longer than we expected. If we were to do this again, we would budget significantly more time for integration and testing rather than treating them as an afterthought.

Working as a pair also taught us how useful it is to explain your thinking out loud. Several times, one of us had been stuck on a bug for a while and simply describing the problem to the other person led to spotting the issue within minutes. Having a second perspective is genuinely valuable, even if the other person has not looked at that specific piece of code before.

## 8. Conclusion

Overall, we are reasonably proud of what we built. The app covers all the required feature areas and works reliably with the kinds of datasets it is intended for. More importantly, the process of building it taught us things that lectures and smaller exercises had not quite managed to — particularly around how a real data pipeline is structured, how to build something that handles errors gracefully, and how to work effectively together under time pressure. We would approach the planning and testing phases differently if we started again, but the experience as a whole has been worthwhile and genuinely useful.