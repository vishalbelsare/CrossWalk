# -*- coding: utf-8 -*-
"""
    data
    ~~~~

    `data` module of the `crosswalk` package.
"""
import numpy as np
import pandas as pd
import warnings
from . import utils


class CWData:
    """Cross Walk data structure.
    """
    def __init__(self,
                 df,
                 obs=None,
                 obs_se=None,
                 alt_dorms=None,
                 ref_dorms=None,
                 covs=None,
                 study_id=None,
                 add_intercept=True):
        """Constructor of CWData

        Args:
            df (pandas.DataFrame):
                Dataframe from csv file that store the data.
            obs (str | None, optional):
                Observations of the problem, can be log or logit differences.
            obs_se (str | None, optional):
                Standard error of the observations.
            alt_dorms (str | None, optional):
                Alternative definitions/methods for each observation.
            ref_dorms (str | None, optional):
                Reference definitions/methods for each observation.
            covs (list{str} | None, optional):
                Covariates linearly parametrized the observation.
            study_id (numpy.ndarray | None, optional):
                Study id for each observation.
            add_intercept (bool, optional):
                If `True`, add intercept to the current covariates.
        """
        self.df = df
        self.obs = None if obs is None else df[obs].values
        self.obs_se = None if obs_se is None else df[obs_se].values
        if alt_dorms is None:
            self.alt_dorms = np.array(['1']*self.df.shape[0])
        else:
            self.alt_dorms = df[alt_dorms].values.astype(str)
        if ref_dorms is None:
            self.ref_dorms = np.array(['0']*self.df.shape[0])
        else:
            self.ref_dorms = df[ref_dorms].values.astype(str)
        self.covs = pd.DataFrame() if covs is None else df[covs].copy()
        self.study_id = None if study_id is None else df[study_id].values

        # dimensions of observations and covariates
        self.num_obs = self.df.shape[0]
        if self.covs.empty and not add_intercept:
            warnings.warn("Covariates must at least include intercept."
                          "Adding intercept automatically.")
            add_intercept = True

        if add_intercept:
            self.covs['intercept'] = np.ones(self.num_obs)

        self.num_covs = self.covs.shape[1]

        # check inputs
        self.check()

        # definition structure
        self.num_dorms, \
        self.dorm_sizes,\
        self.unique_dorms = utils.array_structure(
            np.hstack((self.alt_dorms, self.ref_dorms))
        )
        self.num_alt_dorms, \
        self.alt_dorm_sizes, \
        self.unique_alt_dorms = utils.array_structure(
            self.alt_dorms
        )
        self.num_ref_dorms, \
        self.ref_dorm_sizes, \
        self.unique_ref_dorms = utils.array_structure(
            self.ref_dorms
        )
        self.max_dorm = self.unique_dorms[np.argmax(self.dorm_sizes)]
        self.min_dorm = self.unique_dorms[np.argmin(self.dorm_sizes)]
        self.max_alt_dorm = self.unique_alt_dorms[
            np.argmax(self.alt_dorm_sizes)]
        self.min_alt_dorm = self.unique_alt_dorms[
            np.argmin(self.alt_dorm_sizes)]
        self.max_ref_dorm = self.unique_ref_dorms[
            np.argmax(self.ref_dorm_sizes)]
        self.min_alt_dorm = self.unique_ref_dorms[
            np.argmin(self.ref_dorm_sizes)]

        self.dorm_idx = {
            dorm: i
            for i, dorm in enumerate(self.unique_dorms)
        }

        # study structure
        if self.study_id is None:
            self.num_studies = self.num_obs
            self.study_sizes = np.array([1]*self.num_obs)
            self.unique_study_id = None
        else:
            self.num_studies, \
            self.study_sizes, \
            self.unique_study_id = utils.array_structure(self.study_id)
        self.sort_by_study_id()


    def check(self):
        """Check inputs type, shape and value.
        """
        assert self.obs is None or utils.is_numerical_array(
            self.obs, shape=(self.num_obs,))
        assert self.obs_se is None or utils.is_numerical_array(
            self.obs_se, shape=(self.num_obs,))
        if utils.is_numerical_array(self.obs_se):
            assert (self.obs_se > 0.0).all()

        assert isinstance(self.alt_dorms, np.ndarray)
        assert isinstance(self.ref_dorms, np.ndarray)
        assert self.alt_dorms.shape == (self.num_obs,)
        assert self.ref_dorms.shape == (self.num_obs,)

        assert isinstance(self.covs, pd.DataFrame)
        assert self.covs.shape[1] == self.num_covs

        if self.study_id is not None:
            assert self.study_id.shape == (self.num_obs,)

    def sort_by_study_id(self):
        """Sort the observations and covariates by the study id.
        """
        if self.study_id is not None:
            sort_id = np.argsort(self.study_id)
            self.study_id = self.study_id[sort_id]
            self.obs = self.obs[sort_id]
            self.obs_se = self.obs_se[sort_id]
            self.alt_dorms = self.alt_dorms[sort_id]
            self.ref_dorms = self.ref_dorms[sort_id]
            self.covs = self.covs.reindex(sort_id)

    def copy_dorm_structure(self, cwdata):
        """Copy the dorm structure from other"""
        assert cwdata.num_dorms >= self.num_dorms
        assert all([dorm in cwdata.unique_dorms for dorm in self.unique_dorms])

        self.num_dorms = cwdata.num_dorms
        self.unique_dorms = cwdata.unique_dorms
        self.dorm_idx = cwdata.dorm_idx

    def __repr__(self):
        """Summary of the object.
        """
        dimension_summary = [
            "number of observations: %i" % self.num_obs,
            "number of covariates  : %i" % self.num_covs,
            "number of defs/methods: %i" % self.num_dorms,
            "number of studies     : %i" % self.num_studies,
        ]
        return "\n".join(dimension_summary)
