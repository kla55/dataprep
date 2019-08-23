"""
    This module implements the plot_corr(df) function.
"""
from typing import Any, Optional, Union, Tuple

import math
import dask
import holoviews as hv
import numpy as np
import pandas as pd
from bokeh.io import show
from bokeh.models import HoverTool
from bokeh.models.annotations import Title
from bokeh.models.widgets import Panel, Tabs
from bokeh.plotting import figure, Figure
from scipy.stats import kendalltau
from dataprep.eda.common import Intermediate
from dataprep.utils import _drop_non_numerical_columns, DataType, get_type


def _calc_kendall(
        data_a: np.ndarray,
        data_b: np.ndarray
) -> Any:
    """
    :param data_a: the column of data frame
    :param data_b: the column of data frame
    :return: A float value which indicates the
    correlation of two numpy array
    """
    kendallta, _ = kendalltau(data_a, data_b)
    return kendallta


def _value_to_rank(
        array: np.ndarray
) -> pd.Series:
    """
    :param array: an column of data frame whose
    type is numpy
    :return: translate value to order rank
    """
    array_ranks = pd.Series(array).rank()
    return array_ranks.values


def _discard_unused_visual_elems(
        fig: Figure
) -> None:
    """
    :param fig: A figure object
    :return:
    """
    fig.toolbar_location = None
    fig.toolbar.active_drag = None
    fig.xaxis.axis_label = ''
    fig.yaxis.axis_label = ''


def _vis_correlation_pd(  # pylint: disable=too-many-locals
        intermediate: Intermediate
) -> Tabs:
    """
    :param intermediate: An object to encapsulate the
    intermediate results.
    :return: A figure object
    """
    tab_list = []
    pd_data_frame = intermediate.raw_data['df']
    method_list = intermediate.raw_data['method_list']
    result = intermediate.result
    hv.extension(
        'bokeh',
        logo=False
    )
    for method in method_list:
        corr_matrix = result['corr_' + method[0]]
        name_list = pd_data_frame.columns.values
        data = []
        for i, _ in enumerate(name_list):
            for j, _ in enumerate(name_list):
                data.append((name_list[i],
                             name_list[j],
                             corr_matrix[i, j]))
        tooltips = [
            ('x', '@x'),
            ('y', '@y'),
            ('z', '@z'),
        ]
        hover = HoverTool(tooltips=tooltips)
        heatmap = hv.HeatMap(data).redim.range(z=(-1, 1))
        heatmap.opts(
            tools=[hover],
            colorbar=True,
            width=325,
            title="heatmap_" + method
        )
        fig = hv.render(heatmap, backend='bokeh')
        fig.plot_width = 400
        fig.plot_height = 400
        title = Title()
        title.text = method + ' correlation matrix'
        title.align = 'center'
        fig.title = title
        fig.xaxis.major_label_orientation = math.pi / 2
        _discard_unused_visual_elems(fig)
        tab = Panel(child=fig, title=method)
        tab_list.append(tab)
    tabs = Tabs(tabs=tab_list)
    return tabs


def _vis_correlation_pd_x_k(  # pylint: disable=too-many-locals
        intermediate: Intermediate
) -> Tabs:
    """
    :param intermediate: An object to encapsulate the
    intermediate results.
    :return: A figure object
    """
    result = intermediate.result
    hv.extension('bokeh',
                 logo=False)
    data_p = []
    data_s = []
    data_k = []
    for i, _ in enumerate(result['col_p']):
        data_p.append(('pearson',
                       result['col_p'][i],
                       result['pearson'][i]))
    for i, _ in enumerate(result['col_s']):
        data_s.append(('spearman',
                       result['col_s'][i],
                       result['spearman'][i]))
    for i, _ in enumerate(result['col_k']):
        data_k.append(('kendall',
                       result['col_k'][i],
                       result['kendall'][i]))
    tooltips = [
        ('x', '@x'),
        ('y', '@y'),
        ('z', '@z'),
    ]
    hover = HoverTool(tooltips=tooltips)
    heatmap_p = hv.HeatMap(data_p).redim.range(z=(-1, 1))
    heatmap_p.opts(
        tools=[hover],
        colorbar=True,
        width=325,
        toolbar='above'
    )
    heatmap_s = hv.HeatMap(data_s).redim.range(z=(-1, 1))
    heatmap_s.opts(
        tools=[hover],
        colorbar=True,
        width=325,
        toolbar='above'
    )
    heatmap_k = hv.HeatMap(data_k).redim.range(z=(-1, 1))
    heatmap_k.opts(
        tools=[hover],
        colorbar=True,
        width=325,
        toolbar='above',
    )
    fig_p = hv.render(
        heatmap_p,
        backend='bokeh'
    )
    fig_s = hv.render(
        heatmap_s,
        backend='bokeh'
    )
    fig_k = hv.render(
        heatmap_k,
        backend='bokeh'
    )
    _discard_unused_visual_elems(fig_p)
    _discard_unused_visual_elems(fig_s)
    _discard_unused_visual_elems(fig_k)
    tab_p = Panel(child=fig_p, title='pearson')
    tab_s = Panel(child=fig_s, title='spearman')
    tab_k = Panel(child=fig_k, title='kendall')
    tabs = Tabs(tabs=[tab_p, tab_s, tab_k])
    return tabs


def _vis_correlation_pd_x_y_k(
        intermediate: Intermediate
) -> Figure:
    """
    :param intermediate: An object to encapsulate the
    intermediate results.
    :return: A figure object
    """
    data_x = intermediate.raw_data['df'][
        intermediate.raw_data['x_name']
    ].values
    data_y = intermediate.raw_data['df'][
        intermediate.raw_data['y_name']
    ].values
    result = intermediate.result
    tooltips = [
        ('x', '@x'),
        ('y', '@y'),
    ]
    hover = HoverTool(
        tooltips=tooltips,
        names=['dec', 'inc']
    )
    fig = figure(
        plot_width=400,
        plot_height=400,
        tools=[hover]
    )
    sample_x = np.linspace(min(data_x), max(data_y), 100)
    sample_y = result['line_a'] * sample_x + result['line_b']
    fig.circle(
        data_x,
        data_y,
        size=10,
        color='navy',
        alpha=0.5
    )
    if intermediate.raw_data["k"] is not None:
        for name, color in [("dec", "yellow"), ("inc", "red")]:
            if name == 'inc':
                legend_name = 'most influential (+)'
            else:
                legend_name = 'most influential (-)'
            fig.circle(
                result[f'{name}_point_x'],
                result[f'{name}_point_y'],
                legend=legend_name,
                size=10,
                color=color,
                alpha=0.5,
                name=name,
            )
    else:
        fig.legend.visible = False
    fig.line(
        sample_x,
        sample_y,
        line_width=3
    )
    fig.toolbar_location = None
    fig.toolbar.active_drag = None
    title = Title()
    title.text = 'scatter plot'
    title.align = 'center'
    fig.title = title
    fig.xaxis.axis_label = intermediate.raw_data['x_name']
    fig.yaxis.axis_label = intermediate.raw_data['y_name']
    return fig


def _vis_cross_table(
        intermediate: Intermediate
) -> Figure:
    """
    :param intermediate: An object to encapsulate the
    intermediate results.
    :return: A figure object
    """
    result = intermediate.result
    hv.extension(
        'bokeh',
        logo=False
    )
    cross_matrix = result['cross_table']
    x_cat_list = result['x_cat_list']
    y_cat_list = result['y_cat_list']
    data = []
    for i, _ in enumerate(x_cat_list):
        for j, _ in enumerate(y_cat_list):
            data.append((x_cat_list[i],
                         y_cat_list[j],
                         cross_matrix[i, j]))
    tooltips = [
        ('z', '@z'),
    ]
    hover = HoverTool(tooltips=tooltips)
    heatmap = hv.HeatMap(data)
    heatmap.opts(
        tools=[hover],
        colorbar=True,
        width=325,
        toolbar='above',
        title="cross_table"
    )
    fig = hv.render(
        heatmap,
        backend='bokeh'
    )
    _discard_unused_visual_elems(fig)
    return fig


def _calc_correlation_pd(  # pylint: disable=too-many-locals
        pd_data_frame: pd.DataFrame,
) -> Any:
    """
    :param pd_data_frame: the pandas data_frame for which plots
    are calculated for each column.
    :return: An object to encapsulate the
    intermediate results.
    """
    method_list = ['pearson', 'spearman', 'kendall']
    result = {}
    for method in method_list:
        if method == 'pearson':
            cal_matrix = pd_data_frame.values.T
            cov_xy = np.cov(cal_matrix)
            std_xy = np.sqrt(np.diag(cov_xy))
            corr_matrix = cov_xy / std_xy[:, None] / std_xy[None, :]
            result['corr_p'] = corr_matrix
        elif method == 'spearman':
            cal_matrix = pd_data_frame.values.T
            matrix_row, _ = np.shape(cal_matrix)
            for i in range(matrix_row):
                cal_matrix[i, :] = _value_to_rank(cal_matrix[i, :])
            cov_xy = np.cov(cal_matrix)
            std_xy = np.sqrt(np.diag(cov_xy))
            corr_matrix = cov_xy / std_xy[:, None] / std_xy[None, :]
            result['corr_s'] = corr_matrix
        elif method == 'kendall':
            cal_matrix = pd_data_frame.values.T
            matrix_row, _ = np.shape(cal_matrix)
            corr_matrix = np.ones(
                shape=(matrix_row, matrix_row)
            )
            corr_list = []
            for i in range(matrix_row):
                for j in range(i + 1, matrix_row):
                    tmp = dask.delayed(_calc_kendall)(
                        cal_matrix[i, :], cal_matrix[j, :])
                    corr_list.append(tmp)
            corr_comp = dask.compute(*corr_list)
            idx = 0
            for i in range(matrix_row):  # TODO: Optimize by using numpy api
                for j in range(i + 1, matrix_row):
                    corr_matrix[i][j] = corr_comp[idx]
                    corr_matrix[j][i] = corr_matrix[i][j]
                    idx = idx + 1
            result['corr_k'] = corr_matrix
        else:
            raise ValueError("Method Error")
    raw_data = {
        'df': pd_data_frame,
        'method_list': method_list
    }
    intermediate = Intermediate(result, raw_data)
    return intermediate


def _calc_correlation_pd_k(
        pd_data_frame: pd.DataFrame,
        k: int,
) -> Any:
    """
    :param pd_data_frame: the pandas data_frame for which plots
    are calculated for each column.
    :param k: choose top-k correlation value
    :return: An object to encapsulate the
    intermediate results.
    """
    result = {}
    intermediate_pd = _calc_correlation_pd(
        pd_data_frame=pd_data_frame,
    )
    method_list = intermediate_pd.raw_data['method_list']
    for method in method_list:
        corr_matrix = intermediate_pd.result['corr_' + method[0]]
        matrix_row, _ = np.shape(corr_matrix)
        corr_matrix_re = np.reshape(
            np.triu(corr_matrix, 1),
            (matrix_row * matrix_row,)
        )
        idx = np.argsort(corr_matrix_re)
        mask = np.zeros(
            shape=(matrix_row * matrix_row,)
        )
        for i in range(k):
            if corr_matrix_re[idx[i]] < 0:
                mask[idx[i]] = 1
            if corr_matrix_re[idx[-i - 1]] > 0:
                mask[idx[-i - 1]] = 1
        corr_matrix = np.multiply(corr_matrix_re, mask)
        corr_matrix = np.reshape(
            corr_matrix,
            (matrix_row, matrix_row)
        )
        corr_matrix += corr_matrix.T - np.diag(corr_matrix.diagonal())
        result['corr_' + method[0]] = corr_matrix
        result['mask_' + method[0]] = mask
    raw_data = {
        'df': pd_data_frame,
        'method_list': method_list,
        'k': k
    }
    intermediate = Intermediate(result, raw_data)
    return intermediate


def _calc_correlation_pd_x_k(  # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        pd_data_frame: pd.DataFrame,
        x_name: str,
        value_range: Optional[np.ndarray] = None,
        k: Optional[int] = None,
) -> Intermediate:
    """
    :param pd_data_frame: the pandas data_frame for which plots
    are calculated for each column.
    :param x_name: a valid column name of the data frame
    :param value_range: a range which return correlation
    :param k: choose top-k or reverse top-k
    :return: An object to encapsulate the
    intermediate results.
    """
    if k == 0:
        raise ValueError("k should be larger than 0")
    if k is not None and len(pd_data_frame.columns) < k:
        raise ValueError("k should be smaller than the number of columns")

    name_list = list(pd_data_frame.columns)

    name_idx = name_list.index(x_name)
    cal_matrix = pd_data_frame.values.T
    cal_matrix_p = cal_matrix.copy()
    cal_matrix_s = cal_matrix.copy()
    cal_matrix_k = cal_matrix.copy()

    cov_xy = np.cov(cal_matrix_p)
    std_xy = np.sqrt(np.diag(cov_xy))
    corr_matrix_p = cov_xy / std_xy[:, None] / std_xy[None, :]

    matrix_row, _ = np.shape(cal_matrix_s)
    for i in range(matrix_row):
        cal_matrix_s[i, :] = _value_to_rank(cal_matrix_s[i, :])
    cov_xy = np.cov(cal_matrix_s)
    std_xy = np.sqrt(np.diag(cov_xy))
    corr_matrix_s = cov_xy / std_xy[:, None] / std_xy[None, :]

    matrix_row, _ = np.shape(cal_matrix_k)
    corr_matrix_k = np.ones(
        shape=(matrix_row, matrix_row)
    )
    corr_list = []
    for i in range(0, name_idx):
        tmp = dask.delayed(_calc_kendall)(
            cal_matrix_k[name_idx, :], cal_matrix_k[i, :])
        corr_list.append(tmp)
    for i in range(name_idx + 1, matrix_row):
        tmp = dask.delayed(_calc_kendall)(
            cal_matrix_k[name_idx, :], cal_matrix_k[i, :])
        corr_list.append(tmp)
    corr_comp = dask.compute(*corr_list)
    idx = 0
    for i in range(0, name_idx):
        corr_matrix_k[name_idx][i] = corr_comp[idx]
        corr_matrix_k[i][name_idx] = corr_matrix_k[name_idx][i]
        idx = idx + 1
    for i in range(name_idx + 1, matrix_row):
        corr_matrix_k[name_idx][i] = corr_comp[idx]
        corr_matrix_k[i][name_idx] = corr_matrix_k[name_idx][i]
        idx = idx + 1

    if value_range is not None:
        value_start = value_range.min()
        value_end = value_range.max()
        row_p = corr_matrix_p[name_idx, :]
        idx_p = np.argsort(row_p)
        len_p = len(idx_p)
        start_p = len_p
        end_p = len_p
        for i, _ in enumerate(idx_p):
            if start_p == len_p and \
                    row_p[idx_p[i]] >= value_start:
                start_p = i
            if end_p == len_p and \
                    row_p[idx_p[i]] > value_end:
                end_p = i
        row_s = corr_matrix_s[name_idx, :]
        idx_s = np.argsort(row_s)
        len_s = len(idx_s)
        start_s = len_s
        end_s = len_s
        for i, _ in enumerate(idx_s):
            if start_s == len_s and \
                    row_s[idx_s[i]] >= value_start:
                start_s = i
            if end_s == len_s and \
                    row_s[idx_s[i]] > value_end:
                end_s = i
        row_k = corr_matrix_k[name_idx, :]
        idx_k = np.argsort(row_k)
        len_k = len(idx_k)
        start_k = len_k
        end_k = len_k
        for i, _ in enumerate(idx_k):
            if start_k == len_k and \
                    row_k[idx_k[i]] >= value_start:
                start_k = i
            if end_k == len_k and \
                    row_k[idx_k[i]] > value_end:
                end_k = i
        result = {
            'start_p': start_p,
            'start_s': start_s,
            'start_k': start_k,
            'end_p': end_p,
            'end_s': end_s,
            'end_k': end_k
        }
        raw_data = {
            'df': pd_data_frame,
            'x_name': x_name,
            'value_range': value_range
        }
        if k is not None:
            raw_data['k'] = k
            for method in ['pearson', 'spearman', 'kendall']:
                if result['end_' + method[0]] - result['start_' + method[0]] > k:
                    result['start_' + method[0]] = result['end_' + method[0]] - k
            start_p = result['start_p']
            end_p = result['end_p']
            start_s = result['start_s']
            end_s = result['end_s']
            start_k = result['start_k']
            end_k = result['end_k']
            result['pearson'] = row_p[idx_p[start_p:end_p]]
            result['spearman'] = row_s[idx_s[start_s:end_s]]
            result['kendall'] = row_k[idx_k[start_k:end_k]]
            result['col_p'] = np.array(name_list)[idx_p[start_p:end_p]]
            result['col_s'] = np.array(name_list)[idx_s[start_s:end_s]]
            result['col_k'] = np.array(name_list)[idx_k[start_k:end_k]]
        else:
            start_p = result['start_p']
            end_p = result['end_p']
            start_s = result['start_s']
            end_s = result['end_s']
            start_k = result['start_k']
            end_k = result['end_k']
            result['pearson'] = row_p[idx_p[start_p: end_p]]
            result['spearman'] = row_s[idx_s[start_s: end_s]]
            result['kendall'] = row_k[idx_k[start_k: end_k]]
            result['col_p'] = np.array(name_list)[idx_p[start_p:end_p]]
            result['col_s'] = np.array(name_list)[idx_s[start_s:end_s]]
            result['col_k'] = np.array(name_list)[idx_k[start_k:end_k]]
    else:
        if k is not None:
            row_p = corr_matrix_p[name_idx, :]
            row_p[name_idx] = -1
            idx_p = np.argsort(row_p)
            col_p = np.array(name_list)[idx_p[-k:]]
            col_p = col_p[::-1]
            row_s = corr_matrix_s[name_idx, :]
            row_s[name_idx] = -1
            idx_s = np.argsort(row_s)
            col_s = np.array(name_list)[idx_s[-k:]]
            col_s = col_s[::-1]
            row_k = corr_matrix_k[name_idx, :]
            row_k[name_idx] = -1
            idx_k = np.argsort(row_k)
            col_k = np.array(name_list)[idx_k[-k:]]
            col_k = col_k[::-1]
            result = {
                'pearson': row_p[idx_p[-k:]],
                'spearman': row_s[idx_s[-k:]],
                'kendall': row_k[idx_k[-k:]],
                'col_p': col_p,
                'col_s': col_s,
                'col_k': col_k
            }
            raw_data = {
                'df': pd_data_frame,
                'x_name': x_name,
                'k': k
            }
        else:
            row_p = corr_matrix_p[name_idx, :]
            idx_p = np.argsort(row_p)
            col_p = np.array(name_list)[idx_p]
            col_p = col_p[::-1]
            row_s = corr_matrix_s[name_idx, :]
            idx_s = np.argsort(row_s)
            col_s = np.array(name_list)[idx_s]
            col_s = col_s[::-1]
            row_k = corr_matrix_k[name_idx, :]
            idx_k = np.argsort(row_k)
            col_k = np.array(name_list)[idx_k]
            col_k = col_k[::-1]
            result = {
                'pearson': row_p[idx_p],
                'spearman': row_s[idx_s],
                'kendall': row_k[idx_k],
                'col_p': col_p,
                'col_s': col_s,
                'col_k': col_k
            }
            raw_data = {
                'df': pd_data_frame,
                'x_name': x_name
            }
    intermediate = Intermediate(result, raw_data)
    return intermediate


def _calc_correlation_pd_x_y_k(  # pylint: disable=too-many-locals
        pd_data_frame: pd.DataFrame,
        x_name: str,
        y_name: str,
        k: Optional[int] = None,
) -> Intermediate:
    """
    :param pd_data_frame: the pandas data_frame for which plots
    are calculated for each column.
    :param x_name: a valid column name of the data frame
    :param y_name: a valid column name of the data frame
    :param k: highlight k points which influence pearson correlation most
    :return: An object to encapsulate the
    intermediate results.
    """
    if k == 0:
        raise ValueError("k should be larger than 0")

    data_x = pd_data_frame[x_name].values
    data_y = pd_data_frame[y_name].values
    corr = np.corrcoef(data_x, data_y)[1, 0]
    line_a, line_b = np.linalg.lstsq(
        np.vstack([data_x, np.ones(len(data_x))]).T,
        data_y,
        rcond=None)[0]
    if k is None:
        result = {
            'corr': corr,
            'line_a': line_a,
            'line_b': line_b
        }
        raw_data = {
            'df': pd_data_frame,
            'x_name': x_name,
            'y_name': y_name,
            'k': k
        }
        intermediate = Intermediate(result, raw_data)
        return intermediate

    inc_point_x = []
    inc_point_y = []
    dec_point_x = []
    dec_point_y = []
    inc_mask = np.zeros(len(data_x))
    dec_mask = np.zeros(len(data_x))
    for _ in range(k):
        max_diff_inc = 0
        max_diff_dec = 0
        max_idx_inc = 0
        max_idx_dec = 0
        for j in range(len(data_x)):
            data_x_sel = np.append(data_x[:j], data_x[j + 1:])  # TODO: Avoid copy
            data_y_sel = np.append(data_y[:j], data_y[j + 1:])
            corr_sel = np.corrcoef(data_x_sel, data_y_sel)[1, 0]
            if corr_sel - corr > max_diff_inc and inc_mask[j] != 1:
                max_diff_inc = corr_sel - corr
                max_idx_inc = j
            if corr - corr_sel > max_diff_dec and dec_mask[j] != 1:
                max_diff_dec = corr - corr_sel
                max_idx_dec = j
        inc_mask[max_idx_inc] = 1
        dec_mask[max_idx_dec] = 1
        inc_point_x.append(data_x[max_idx_inc])
        inc_point_y.append(data_y[max_idx_inc])
        dec_point_x.append(data_x[max_idx_dec])
        dec_point_y.append(data_y[max_idx_dec])
    result = {
        'corr': corr,
        'dec_point_x': dec_point_x,
        'dec_point_y': dec_point_y,
        'inc_point_x': inc_point_x,
        'inc_point_y': inc_point_y,
        'line_a': line_a,
        'line_b': line_b
    }
    raw_data = {
        'df': pd_data_frame,
        'x_name': x_name,
        'y_name': y_name,
        'k': k
    }
    intermediate = Intermediate(result, raw_data)
    return intermediate


def _calc_cross_table(  # pylint: disable=too-many-locals
        pd_data_frame: pd.DataFrame,
        x_name: str,
        y_name: str
) -> Intermediate:
    """
    :param pd_data_frame: the pandas data_frame for which plots
    are calculated for each column.
    :param x_name: a valid column name of the data frame
    :param y_name: a valid column name of the data frame
    :return: An object to encapsulate the
    intermediate results.
    """
    x_cat_list = list(pd_data_frame[x_name].cat.categories)
    y_cat_list = list(pd_data_frame[y_name].cat.categories)
    dict_x_cat = {x_cat_list[i]: i for i, _ in enumerate(x_cat_list)}
    dict_y_cat = {y_cat_list[i]: i for i, _ in enumerate(y_cat_list)}
    cross_matrix = np.zeros(
        shape=(len(x_cat_list),
               len(y_cat_list))
    )
    x_value_list = pd_data_frame[x_name].values
    y_value_list = pd_data_frame[y_name].values
    for i, _ in enumerate(x_value_list):
        x_pos = dict_x_cat[x_value_list[i]]
        y_pos = dict_y_cat[y_value_list[i]]
        cross_matrix[x_pos][y_pos] = cross_matrix[x_pos][y_pos] + 1
    result = {
        'cross_table': cross_matrix,
        'x_cat_list': x_cat_list,
        'y_cat_list': y_cat_list
    }
    raw_data = {
        'df': pd_data_frame,
        'x_name': x_name,
        'y_name': y_name
    }
    intermediate = Intermediate(result, raw_data)
    return intermediate


def plot_correlation(  # pylint: disable=too-many-arguments
        pd_data_frame: pd.DataFrame,
        x_name: Optional[str] = None,
        y_name: Optional[str] = None,
        value_range: Optional[np.ndarray] = None,
        k: Optional[int] = None,
        return_intermediate: bool = False
) -> Union[Union[Figure, Tabs],
           Tuple[Union[Figure, Tabs], Any]]:
    """
    :param pd_data_frame: the pandas data_frame for which plots are calculated for each
    column.
    :param x_name: a valid column name of the data frame
    :param y_name: a valid column name of the data frame
    :param value_range: range of value
    :param k: choose top-k element
    :param return_intermediate: whether show intermediate results to users
    :return: A (column: [array/dict]) dict to encapsulate the
    intermediate results.

    match (x_name, y_name, k)
        case (None, None, None) => heatmap
        case (Some, None, Some) => Top K columns for (pearson, spearman, kendall)
        case (Some, Some, _) => Scatter with regression line with/without top k outliers
        otherwise => error
    """
    if x_name is not None and y_name is not None:
        if get_type(pd_data_frame[x_name]) == DataType.TYPE_CAT and \
                get_type(pd_data_frame[y_name]) == DataType.TYPE_CAT:
            intermediate = _calc_cross_table(
                pd_data_frame=pd_data_frame,
                x_name=x_name,
                y_name=y_name
            )
            fig = _vis_cross_table(
                intermediate=intermediate
            )
        elif not get_type(pd_data_frame[x_name]) != DataType.TYPE_NUM and \
                not get_type(pd_data_frame[y_name]) != DataType.TYPE_NUM:
            intermediate = _calc_correlation_pd_x_y_k(
                pd_data_frame=pd_data_frame,
                x_name=x_name,
                y_name=y_name,
                k=k
            )
            fig = _vis_correlation_pd_x_y_k(
                intermediate=intermediate
            )
        else:
            raise ValueError("Cannot calculate the correlation "
                             "between two different dtype column")
    elif x_name is not None:
        if get_type(pd_data_frame[x_name]) != DataType.TYPE_NUM:
            raise ValueError("The dtype of data frame column "
                             "should be numerical")
        pd_data_frame = _drop_non_numerical_columns(
            pd_data_frame=pd_data_frame
        )
        intermediate = _calc_correlation_pd_x_k(
            pd_data_frame=pd_data_frame,
            x_name=x_name,
            value_range=value_range,
            k=k
        )
        fig = _vis_correlation_pd_x_k(
            intermediate=intermediate
        )
    elif x_name is None and y_name is not None:
        raise ValueError("Please give a value to x_name")
    elif k is not None:
        pd_data_frame = _drop_non_numerical_columns(
            pd_data_frame=pd_data_frame
        )
        intermediate = _calc_correlation_pd_k(
            pd_data_frame=pd_data_frame,
            k=k
        )
        fig = _vis_correlation_pd(
            intermediate=intermediate
        )
    else:
        pd_data_frame = _drop_non_numerical_columns(
            pd_data_frame=pd_data_frame
        )
        intermediate = _calc_correlation_pd(
            pd_data_frame=pd_data_frame
        )
        fig = _vis_correlation_pd(
            intermediate=intermediate
        )
    show(fig)
    if return_intermediate:
        return fig, intermediate
    return fig