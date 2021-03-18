import re
import io
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import plotly.express as px
import base64
import streamlit as st
import numpy as np
import pandas as pd



def V2nm(V):
  
    ##This function converts applied voltage to nm based on the piezoscanner calibration in the software
    gain = 20
    dist=gain*V*15.21
    return(dist)

@st.cache(allow_output_mutation=True)
def load_file(path):
    '''
    This function will parse a standard HEKA .asc file into a pandas dataframe.

    Arguments: 
    path - a stringIO input of a standard HEKA output .asc file.

    Returns:
    df, dfcache - two copies of the file reformatted into a dataframe.
    '''

    lineIndices = []                                 
    rawFile = path.getvalue().strip().split("\n")         # Splits string at \n and removes trailing spaces

    count=0                                               
    for line in rawFile:                                  # Finds rows that contain header information to exclude from df
        if re.search(r"[a-z]+", line) == None:           
            lineIndices.append(count)                     
        count += 1                                    
    
    processedFile = [rawFile[i].strip().replace(" ", "").split(",") for i in lineIndices]     # Formats headerless file for later df

    nSweeps = int((len(rawFile)-len(processedFile)-1)/2)   # Use the difference in file with and without headers to find nSweeps

    df = pd.DataFrame(columns=['index','ti','i','tv','v','tin0','in0','tz','z','tlat','lat'], data=processedFile)
    df = df.apply(pd.to_numeric)
    df = df.dropna(axis=0)
    df['sweep'] = np.repeat(np.arange(nSweeps), len(df)/nSweeps)
    df[['ti','tin0','tv','tz','tlat']] = df[['ti','tin0','tv','tz','tlat']].multiply(1000)
    df['position'] = V2nm(df['z'])
    
    # Change units to something easier to work with

    df_cache = df.copy()

    return df, df_cache


def split_trace(df):
    #Use the peak of the Z-motor position voltage signal to separate the approach and retract curves
    sub = df[df['tin0']<= 400]
    peak = sub.loc[:,'z'].idxmax()
    approach = sub[1:peak]
    retract = sub[peak:np.shape(sub)[0]]

    return(approach,retract)


@st.cache(allow_output_mutation=True)
def plot_sweeps(df):
  
    '''
    This function will plot a dataframe of sweeps using plotly with hidden axis.

    Arguments: 
    df - a dataframe with columns tp, p, ti, i, and sweep

    Returns:
    fig - a plotly figure object
    '''

    fig = make_subplots(rows=2, cols=1,  row_width=[0.6, 0.3])

    fig.add_trace(
      go.Scatter(mode='lines', x=df.tin0, y=df.in0,
                 marker=dict(color='blue'),
                 hovertemplate='x: %{x}<br>' + 'y: %{y}<br>'),
                 row=1, col=1)

    fig.add_trace(
      go.Scatter(mode='lines', x=df.tz, y=df.z, marker=dict(color='green'),
                hovertemplate='x: %{x}<br>' + 'y: %{y}<br>'),
                row=1, col=1)

    fig.add_trace(
      go.Scatter(mode='lines', x=df.tlat, y=df.lat, marker=dict(color='orange'),
                hovertemplate='x: %{x}<br>' + 'y: %{y}<br>'),
                row=1, col=1)

    [approach, retract] = split_trace(df)

    fig.add_trace(
      go.Scatter(mode='lines', x=approach.position, y=approach.in0, marker=dict(color='black'),
                hovertemplate='x: %{x}<br>' + 'y: %{y}<br>'),
                row=2, col=1)

    fig.update_xaxes(title_text="Time (ms)", row=1, col=1)
    fig.update_yaxes(title_text="Voltage (V)", row=1, col=1)
    fig.update_xaxes(title_text="Position (nm)", row=2, col=1)
    fig.update_yaxes(title_text="Voltage (V)", row=2, col=1)

    fig.update_layout(
         height=600,
         width=800,
         template='simple_white',
         showlegend=False,
         hovermode='closest')

    return(fig)
        

def highlight_fig(fig, window):
    '''
    This function will highlight a selected region of the plot.

    Arguments: 
    fig - a plotly figure object.
    window - an iterable with the start and end of the selection window.
    draw - boolean indicating whether or not to draw a highlight (default is False).
    Returns:
    fig - a plotly figure object
    '''

    highlight_color = "LightBlue"
    fig.update_layout(
        shapes=[
            dict(
                type="rect",
                xref="x2",
                yref="paper",
                x0=window[0],
                x1=window[1],
                fillcolor=highlight_color,
                opacity=0.5,
                layer="below",
                line_width=0,
                )
            ]
        )
    return(fig)


def linear_fit(x, m, b):
    '''
    This function defines a sigmoid curve.

    Arguments: 
    p - the abscissa data.
    p50 - the inflection point of the sigmoid.
    k - the slope at the inflection point of a sigmoid.
    
    Returns:
    The ordinate for a boltzmann sigmoid with the passed parameters.
    '''

    return(m * x + b)


def fit_layer(df, fig, fit):
    '''
    This function plots fit data over an existing plot.

    Arguments: 
    df - a pandas dataframe with columns pressure, param, and normalized_param.
    fig - a plotly figure object.
    fit - the fit parameters for a sigmoid fit.
    
    Returns:
    df - a plotly figure object.
    '''

    xfine = np.linspace(min(df.position),max(df.position), 100)
    fig.add_trace(
    go.Scatter(mode='lines',
               name='fit', 
               marker_color='red', 
               marker_line_width = 1,
               x=xfine, 
               y=linear_fit(xfine, *fit),
               hovertemplate='x: %{x}<br>' + 'y: %{y}<br>'
               ),
               row=2, col=1
    )

    return(fig)


