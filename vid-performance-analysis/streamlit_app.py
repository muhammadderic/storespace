#import relevant libraries (visualization, dashboard, data manipulation)
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import datetime

aggregated_metrics_by_country_and_subs = 'Aggregated_Metrics_By_Country_And_Subscriber_Status.csv'
aggregated_metrics_by_video = 'Aggregated_Metrics_By_Video.csv'
all_comments_final = 'All_Comments_Final.csv'
video_performance_over_time = 'Video_Performance_Over_Time.csv'

#Define Functions 
def style_negative(v, props=''):
    """ Style negative values in dataframe"""
    try: 
        return props if v < 0 else None
    except:
        pass
    
def style_positive(v, props=''):
    """Style positive values in dataframe"""
    try: 
        return props if v > 0 else None
    except:
        pass    
    
def audience_simple(country):
    """Show top represented countries"""
    if country == 'US':
        return 'USA'
    elif country == 'IN':
        return 'India'
    else:
        return 'Other'
    
am_ctsubs = pd.read_csv(aggregated_metrics_by_country_and_subs)
am_vid = pd.read_csv(aggregated_metrics_by_video)
acom_f = pd.read_csv(all_comments_final)
vid_pot = pd.read_csv(video_performance_over_time)

# ===== DATA PREPROCESSING =====
# === Aggregated Metrics by Video Dataset ===
# Remove the first row of the dataset
am_vid = am_vid.iloc[1:,:].copy()

# Change the initial column names
am_vid.columns = ['Video','Video title','Video publish time','Comments added','Shares','Dislikes','Likes',
                      'Subscribers lost','Subscribers gained','RPM(USD)','CPM(USD)','Average % viewed','Average view duration',
                      'Views','Watch time (hours)','Subscribers','Your estimated revenue (USD)','Impressions','Impressions ctr(%)']

# Change the 'Video publish time' column into datetime
am_vid['Video publish time'] = pd.to_datetime(am_vid['Video publish time'], format='%b %d, %Y')

# Apply striptime with hour:minute:second format to 'Average view duration'
am_vid['Average view duration'] = am_vid['Average view duration'].apply(lambda x: datetime.strptime(x,'%H:%M:%S'))

# Create new column that contains average view duration in second
am_vid['Avg_duration_sec'] = am_vid['Average view duration'].apply(lambda x: x.second + x.minute*60 + x.hour*3600)

# Create engagement ratio
am_vid['Engagement_ratio'] = (am_vid['Comments added'] + am_vid['Shares'] + am_vid['Dislikes'] + am_vid['Likes']) / am_vid.Views

# Create views per sub-gained data
am_vid['Views / sub gained'] = am_vid['Views'] / am_vid['Subscribers gained']

# Sort the data based on time of video published
am_vid.sort_values('Video publish time', ascending = False, inplace = True) 

# === Video Performance Over Time Dataset ===
# Change date column into datetime
# errors='coerce' used to handle any dates that don’t match with the format
vid_pot['Date'] = pd.to_datetime(vid_pot['Date'], dayfirst=True, errors='coerce')


# ===== ADDITIONAL DATA ENGINEERING FOR AGGREGATED DATA =====
am_vid_diff = am_vid.copy()

# This line of code is calculating the date that is 12 months earlier 
# than the most recent (maximum) date in the Video publish time column. 
# This is likely useful if you want to filter or analyze data for the last 12 months.
metric_date_12mo = am_vid_diff['Video publish time'].max() - pd.DateOffset(months=12)
print("METRIC DATE 12 MONTHS EARLIER: ", metric_date_12mo)

# gives the median of numerical columns for videos published in the last 12 months
median_agg = am_vid_diff[am_vid_diff['Video publish time'] >= metric_date_12mo].select_dtypes(include='number').median()

# Get all numeric and float columns
numeric_cols = np.array((am_vid_diff.dtypes == 'float64') | (am_vid_diff.dtypes == 'int64'))

# Get median value from numeric and float data in 12 last months
am_vid_diff.iloc[:,numeric_cols] = (am_vid_diff.iloc[:,numeric_cols] - median_agg).div(median_agg)


# ===== ADDITIONAL DATA ENGINEERING FOR VIDEO PERFORMANCE OVER TIME =====
# Merge daily data with publish data to get delta 
vid_pot_diff = pd.merge(vid_pot, am_vid.loc[:,['Video','Video publish time']], left_on ='External Video ID', right_on = 'Video')
vid_pot_diff['days_published'] = (vid_pot_diff['Date'] - vid_pot_diff['Video publish time']).dt.days

# Get last 12 months of data rather than all data 
date_12mo = am_vid['Video publish time'].max() - pd.DateOffset(months =12)
df_time_diff_yr = vid_pot_diff[vid_pot_diff['Video publish time'] >= date_12mo]


# ===== GET DAILY VIEW DATA (First 30), MEDIAN, AND PERCENTILES =====
# views_days = pd.pivot_table(df_time_diff_yr, 
#                             index='days_published', 
#                             values='Views', 
#                             aggfunc=['mean', 'median', 
#                                      lambda x: np.percentile(x, 80), 
#                                      lambda x: np.percentile(x, 20)]
#                            ).reset_index()
# views_days.columns = ['days_published','mean_views','median_views','80pct_views','20pct_views']
# views_days = views_days[views_days['days_published'].between(0,30)]
# views_cumulative = views_days.loc[:,['days_published','median_views','80pct_views','20pct_views']] 
# views_cumulative.loc[:,['median_views',
#                         '80pct_views',
#                         '20pct_views']] = views_cumulative.loc[:,['median_views','80pct_views','20pct_views']].cumsum()


###############################################################################
#Start building Streamlit App
###############################################################################

add_sidebar = st.sidebar.selectbox('Aggregate or Individual Video', ('Aggregate Metrics','Individual Video Analysis'))

#Show individual metrics 
if add_sidebar == 'Aggregate Metrics':
    st.write("Ken Jee YouTube Aggregated Data")
    
    am_vid_metrics = am_vid[['Video publish time','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed',
                             'Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
    metric_date_6mo = am_vid_metrics['Video publish time'].max() - pd.DateOffset(months =6)
    metric_date_12mo = am_vid_metrics['Video publish time'].max() - pd.DateOffset(months =12)
    metric_medians6mo = am_vid_metrics[am_vid_metrics['Video publish time'] >= metric_date_6mo].median()
    metric_medians12mo = am_vid_metrics[am_vid_metrics['Video publish time'] >= metric_date_12mo].median()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    columns = [col1, col2, col3, col4, col5]
    
    count = 0
    for i in metric_medians6mo.index:
        with columns[count]:
            if isinstance(metric_medians6mo[i], pd.Timestamp) and isinstance(metric_medians12mo[i], pd.Timestamp):
                # Calculate the difference (Timedelta)
                delta = metric_medians6mo[i] - metric_medians12mo[i]

                print("DELTA: ", delta)

                # # Convert Timedelta to total seconds for division
                delta_in_seconds = delta.total_seconds()

                # # Convert the reference timestamp to seconds
                reference_in_seconds = metric_medians12mo[i].timestamp()
                
                # # Calculate the relative difference
                delta = delta_in_seconds / reference_in_seconds

                st.metric(label= i, value = metric_medians6mo[i].strftime('%Y-%m-%d %H:%M:%S'), delta = "{:.2%}".format(delta))
            else:
                delta = (metric_medians6mo[i] - metric_medians12mo[i])/metric_medians12mo[i]
                st.metric(label= i, value = round(metric_medians6mo[i],1), delta = "{:.2%}".format(delta))
            count += 1
            if count >= 5:
                count = 0
    #get date information / trim to relevant data 
    am_vid_diff['Publish_date'] = am_vid_diff['Video publish time'].apply(lambda x: x.date())
    am_vid_diff_final = am_vid_diff.loc[:,['Video title','Publish_date','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed',
                             'Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
    
    # Select only numeric columns
    numeric_cols = am_vid_diff_final.select_dtypes(include='number')

    # Calculate the median for numeric columns
    medians = numeric_cols.median()

    # Get the column names (indices) as a list
    am_vid_numeric_lst = medians.index.tolist()

    # am_vid_numeric_lst = am_vid_diff_final.median().index.tolist()
    df_to_pct = {}
    for i in am_vid_numeric_lst:
        df_to_pct[i] = '{:.1%}'.format
    
    st.dataframe(am_vid_diff_final.style.hide_index().applymap(style_negative, props='color:red;').applymap(style_positive, props='color:green;').format(df_to_pct))
    # st.dataframe(am_vid_diff_final.style.hide().applymap(style_negative).applymap(style_positive).format(df_to_pct))
    
# if add_sidebar == 'Individual Video Analysis':
#     videos = tuple(am_vid['Video title'])
#     st.write("Individual Video Performance")
#     video_select = st.selectbox('Pick a Video:', videos)
    
#     agg_filtered = am_vid[am_vid['Video title'] == video_select]
#     agg_sub_filtered = am_ctsubs[am_ctsubs['Video Title'] == video_select]
#     agg_sub_filtered['Country'] = agg_sub_filtered['Country Code'].apply(audience_simple)
#     agg_sub_filtered.sort_values('Is Subscribed', inplace= True)   
    
#     fig = px.bar(agg_sub_filtered, x ='Views', y='Is Subscribed', color ='Country', orientation ='h')
#     #order axis 
#     st.plotly_chart(fig)
    
#     agg_time_filtered = vid_pot_diff[vid_pot_diff['Video Title'] == video_select]
#     first_30 = agg_time_filtered[agg_time_filtered['days_published'].between(0,30)]
#     first_30 = first_30.sort_values('days_published')
    
#     fig2 = go.Figure()
#     fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['20pct_views'],
#                     mode='lines',
#                     name='20th percentile', line=dict(color='purple', dash ='dash')))
#     fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['median_views'],
#                         mode='lines',
#                         name='50th percentile', line=dict(color='black', dash ='dash')))
#     fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['80pct_views'],
#                         mode='lines', 
#                         name='80th percentile', line=dict(color='royalblue', dash ='dash')))
#     fig2.add_trace(go.Scatter(x=first_30['days_published'], y=first_30['Views'].cumsum(),
#                         mode='lines', 
#                         name='Current Video' ,line=dict(color='firebrick',width=8)))
        
#     fig2.update_layout(title='View comparison first 30 days',
#                    xaxis_title='Days Since Published',
#                    yaxis_title='Cumulative views')
    
#     st.plotly_chart(fig2)