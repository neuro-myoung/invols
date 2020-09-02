from app_scripts import *
from scipy.optimize import curve_fit
import streamlit as st
import numpy as np
import pandas as pd


## Page setup
st.beta_set_page_config(
    page_title="Ephys Analysis",
    page_icon="🧊")

st.set_option('deprecation.showfileUploaderEncoding', False)
st.sidebar.subheader('Data:')
st.sidebar.markdown("Drag and drop HEKA .asc export files. Keep table display at 'None' when not in use for performance.")
data = st.sidebar.file_uploader("", type=["csv", "asc", "txt"])

## Display a warning and stop run if there is no data uploaded
if data is None:
    st.warning('Upload a file to run the app...')
    st.stop()


st.title('Sensitivity Analysis')

## Load HEKA data file
[df, df_cache] = load_file(data)

## Recover original dataframe and start over
if st.sidebar.button('Reset Data'):
    df = df_cache

## Check parts of the data
tableDisplay = st.sidebar.selectbox(
    'Table Display:',
    ('None', 'Head', 'Tail', 'All'))

if tableDisplay == 'Head':
    st.dataframe(df.head(10))
elif tableDisplay == 'Tail':
    st.dataframe(df.tail(10))
elif tableDisplay == 'All':
    st.dataframe(df)

st.sidebar.markdown('---')

## Select single sweeps, fit windows, and perform + overlay the fit
sweep = st.sidebar.selectbox(
    'Select sweep to analyze:',
    np.unique(df.sweep))

df_sub = df.query('sweep == @sweep')
[approach, retract] = split_trace(df_sub)

## Make initial plot and set plot area
fig = plot_sweeps(df_sub)
plot_area = st.empty()

st.sidebar.markdown('Type in the window in ms over which to perform a linear fit.')

## Establish fit window
start = int(st.sidebar.text_input('Start', 0))
end = int(st.sidebar.text_input('End', 0))

if (start != 0) & (end != 0):
  highlight_fig(fig, (start, end))

## Perform fit
if st.sidebar.button('Fit line'):
  fitArea = approach.query('position >= @start and position <= @end')
  popt, pcov = curve_fit(linear_fit, fitArea.position, fitArea.in0)
  fig = fit_layer(fitArea, fig, popt)
  st.subheader(f'Sensitivity: {round(1/popt[0],2)} nm/V')

## Final plot
plot_area.plotly_chart(fig)












