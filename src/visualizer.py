import matplotlib.pyplot as plt

def setup_plot_style():
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.titlesize'] = 13