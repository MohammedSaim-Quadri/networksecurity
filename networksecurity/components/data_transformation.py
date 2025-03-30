import sys,os
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.pipeline import Pipeline
from networksecurity.constant.training_pipeline import TARGET_COLUMN
from networksecurity.constant.training_pipeline import DATA_TRANSFORMATION_IMPUTER_PARAMS

from networksecurity.entity.artifact_entity import (DataTransformationArtifact, DataValidationArtifact)
from networksecurity.entity.config_entity import DataTransformationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from networksecurity.utils.main_utils.utils import save_numpy_array, save_object


class DataTransformation:
    def __init__(self,data_validation_artifact:DataValidationArtifact,
                data_transformation_config:DataTransformationConfig):
        try:
            self.data_validation_artifact:DataValidationArtifact = data_validation_artifact
            self.data_transformation_config:DataTransformationConfig = data_transformation_config
        except Exception as e:
            raise NetworkSecurityException(e,sys)
        

    @staticmethod
    def read_data(file_path)->pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e,sys)
        

    def get_transformer_object(cls)->Pipeline:
        """
        It initialises a KNNImputer object with the parameters specified in the training_pipeline.py file
        and returns a Pipeline object with the KNNImputer object as the first step.
        Args:
        cls: DataTransformation
        Returns:
        A Pipeline object
        """
        logging.info("Entered get transformer method of the DataTransformation class")
        try:
            imputer:KNNImputer=KNNImputer(**DATA_TRANSFORMATION_IMPUTER_PARAMS)
            logging.info(
                f"Initialized KNNImputer with {DATA_TRANSFORMATION_IMPUTER_PARAMS}"
            )
            processor:Pipeline = Pipeline([("imputer",imputer)])
            return processor
        except Exception as e:
            raise NetworkSecurityException(e,sys)
        

    def initiate_data_transformation(self)-> DataTransformationArtifact:
        logging.info("Entered initiate data transformation method of DataTransformation class")
        try:
            logging.info("starting data transformation")
            train_df = DataTransformation.read_data(self.data_validation_artifact.valid_train_file_path)
            test_df = DataTransformation.read_data(self.data_validation_artifact.valid_test_file_path)

            # training dataframe
            input_feature_train = train_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_train = train_df[TARGET_COLUMN]
            target_feature_train = target_feature_train.replace(-1,0)

            # test dataframe
            input_feature_test = test_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_test = test_df[TARGET_COLUMN]
            target_feature_test = target_feature_test.replace(-1,0)

            preprocessor = self.get_transformer_object()

            preprocessor_obj = preprocessor.fit(input_feature_train)
            transformed_input_feature_train = preprocessor_obj.transform(input_feature_train)
            transformed_input_feature_test = preprocessor_obj.transform(input_feature_test)

            train_arr = np.c_[transformed_input_feature_train, np.array(target_feature_train)]
            test_arr = np.c_[transformed_input_feature_test, np.array(target_feature_test)]

            # save numpy array
            save_numpy_array(self.data_transformation_config.transformed_train_file_path, array= train_arr)
            save_numpy_array(self.data_transformation_config.transformed_test_file_path, array=test_arr)
            save_object(self.data_transformation_config.transformed_object_file_path, preprocessor_obj)

            save_object("final_models/preprocessor.pkl", preprocessor_obj)

            # preparing artifacts 
            data_transformation_artifact = DataTransformationArtifact(
                transformed_object_file_path=self.data_transformation_config.transformed_object_file_path,
                transformed_train_file_path=self.data_transformation_config.transformed_train_file_path,
                transformed_test_file_path=self.data_transformation_config.transformed_test_file_path
            )

            return data_transformation_artifact

        except Exception as e:
            raise NetworkSecurityException(e,sys)