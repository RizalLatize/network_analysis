#!/usr/bin/env python
# coding: utf-8

# In[2]:

# cd C:\Latize\Rizal_Analytics\Network_Analysis
# streamlit run streamlit_network_analysis.py 
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import networkx as nx
from pyvis.network import Network
import community.community_louvain #pip install python-louvain

# Read dataset (CSV)
#df = pd.read_csv('processed_drug_interactions.csv')
#df.head()

import pandas as pd
import numpy as np

from pandasql import sqldf

import random
random.seed(10)



#===================================== FOR ZY =============================================
st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

def authenticate_user():
    if 'authenticated' not in st.session_state:
        st.text_input(label='Username:',value='',key='user',on_change=creds_entered)
        st.text_input(label='Password:',value='',key='passwd',type='password',on_change=creds_entered)
        return False
    else:
        if st.session_state['authenticated']:
            return True
        else:
            st.text_input(label='Username:',value='',key='user',on_change=creds_entered)
            st.text_input(label='Password:',value='',key='passwd',type='password',on_change=creds_entered)
            return False    

def creds_entered():
    if st.session_state['user'].strip()=='aml_analyst' and st.session_state['passwd'].strip()=='aml321':
        st.session_state['authenticated'] = True
    else:
        st.session_state['authenticated'] = False
        if not st.session_state['passwd']:
            st.warning('Please enter password.')
        elif not st.session_state['user']:
            st.warning('Please enter username.')
        else:
            st.error('Invalid Username/Password!')

if authenticate_user():
#=============================== END ZY ============================================================

  # Set header title
  st.title('Social Network Graph')
  
  uploaded_file = st.file_uploader("Choose a CSV file")#, accept_multiple_files=True)
  
     
  if uploaded_file is not None:
      df = pd.read_csv(uploaded_file,usecols=['from','to'])
      
      
      #df['weight']=1
      labels = ['friend','rival','acquaintance']#,'best_friend']
      df['label'] = random.choices(labels,weights=None,k=len(df))
      weight = [2,4,8,16,32]
      df['weight'] = random.choices(weight,weights=None,k=len(df))
      df['title'] = df['label']
  
  
  
      agg_label_df = sqldf("""
                      SELECT 
                      label
                      ,COUNT(label) AS counts
                      FROM df
                      GROUP BY label
                      ORDER BY counts DESC
  
                      """,locals())
      #agg_label_df
      
      st.dataframe(agg_label_df)#,use_container_width=True)
  
      agg_from_df = sqldf("""
                  SELECT 
                  `from`
                  ,label
                  ,COUNT(`to`) AS counts
                  FROM df
                  GROUP BY `from`
                  ,label
                  ORDER BY counts DESC
  
                  """,locals())
      #agg_from_df
  
      uniq = sorted(list(set([*df['from'],*df['to']])))
  
      relationships= sorted(list(df['label'].unique()))
  
  
  
  
  
  
  
  
  
      # Define list of selection options and sort alphabetically
      # Implement multiselect dropdown menu for option selection (returns a list)
      relation = st.multiselect('Select relationships to visualize', relationships,'rival')
  
  
      # In[ ]:
  
  
      # Set info message on initial site load
      if len(relation) == 0:
          st.text('Choose at least 1 relationship to start')
  
      # Create network graph when user selects >= 1 item
      else:
          df_select = df.loc[df['label'].isin(relation) ]
          df_select = df_select.reset_index(drop=True)
  
    
  
          G = nx.from_pandas_edgelist(df_select, 
                                  source = "from", 
                                  target = "to", 
                                  edge_attr = True, 
                                  create_using = nx.Graph())
      
          communities =  community.community_louvain.best_partition(G,random_state=123) 
          communities_df = pd.DataFrame.from_dict(communities, orient='index', columns=['community']).reset_index()
          communities_df = communities_df.rename(columns={'index':'from'})
          
          df_select2= sqldf("""
                              SELECT 
                              a.`from`
                              ,a.`to`
                              ,a.label
                              ,a.weight
                              ,b.community
                              FROM df_select a
                              LEFT JOIN communities_df b
                              ON a.`from` = b.`from`
                              """,locals())
  
          agg_community_df = sqldf("""
                          SELECT 
                          `from`
                          ,label
                          ,COUNT(label) AS counts
                          ,community
                          ,GROUP_CONCAT(`to`) AS connected_parties
                          FROM df_select2
                          GROUP BY `from`,label,community
                          ORDER BY counts DESC
                          """,locals())
          
          st.dataframe(agg_community_df,use_container_width=True)
          
          
          
          uniq_community = sorted(list(agg_community_df['community'].unique()))
          
          
          
          if len(uniq_community) > 0:
              select_community = st.multiselect('Select community to visualize', uniq_community)
              
              if len(select_community)==0:
                  st.text('Choose at least 1 community to start')
              
              else:
                  dfg = df_select2.loc[df_select2['community'].isin(select_community)]
                  dfg['title'] = dfg['community']
                  
  
                  dfg_tbl = dfg[['from','to','label','community']].copy()
                  dfg = dfg.rename(columns={'community':'group'})
                  
                  G = nx.from_pandas_edgelist(dfg, 
                                  source = "from", 
                                  target = "to", 
                                  edge_attr = True, 
                                  create_using = nx.Graph())
  
                  # Initiate PyVis network object
                  net = Network(notebook = True
                                ,cdn_resources='remote'
                                ,width= '100%'#width="1000px"
                                ,height="1000px"
                                ,select_menu=True
                                ,filter_menu=True
                                , bgcolor='#222222', font_color='white'
                               )
  
                  node_degree = dict(G.degree)
  
                  #Setting up node size attribute
                  nx.set_node_attributes(G, node_degree, 'size')
  
                  #import community as community_louvain
                  #communities =  community.community_louvain.best_partition(G) #community_louvain.best_partition(G)
                  nx.set_node_attributes(G, communities, 'group')
  
                  # Take Networkx graph and translate it to a PyVis graph format
                  net.from_nx(G)
  
                  # Generate network with specific layout settings
                  net.repulsion(node_distance=420,
                              central_gravity=0.33,
                              spring_length=110,
                              spring_strength=0.10,
                              damping=0.95)
  
                  net.save_graph('test_streamlit_pyvis.html')
                  HtmlFile = open('test_streamlit_pyvis.html', 'r', encoding='utf-8')
  
  
  
                  # Load HTML file in HTML component for display on Streamlit page
                  components.html(HtmlFile.read(), height=1000)
                  
                  dfg_tbl = dfg_tbl.rename(columns={'label':'relationship'})
                  st.dataframe(dfg_tbl,use_container_width=True)
        
        
        


   




