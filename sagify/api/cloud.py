# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json
import os

from sagify.config.config import ConfigManager
from sagify.sagemaker import sagemaker


def _read_config(input_dir):
    config_file_path = os.path.join(input_dir, 'sagify', 'config.json')
    if not os.path.isfile(config_file_path):
        raise ValueError("This is not a sagify directory: {}".format(input_dir))

    return ConfigManager(config_file_path).get_config()


def _read_hyperparams_config(hyperparams_file_path):
    if not os.path.isfile(hyperparams_file_path):
        raise ValueError(
            "The given hyperparams file {} doens't exist".format(hyperparams_file_path)
        )

    with open(hyperparams_file_path) as _in_file:
        return json.load(_in_file)


def upload_data(dir, input_dir, s3_dir):
    """
    Uploads data to S3

    :param dir: [str], source root directory
    :param input_dir: [str], path to local data input directory
    :param s3_dir: [str], S3 location to upload data

    :return: [str], S3 location to upload data
    """
    config = _read_config(dir)
    sage_maker_client = sagemaker.SageMakerClient(config.aws_profile, config.aws_region)

    return sage_maker_client.upload_data(input_dir, s3_dir)


def train(
        dir,
        input_s3_dir,
        output_s3_dir,
        hyperparams_file,
        ec2_type,
        volume_size,
        time_out,
        docker_tag,
        aws_role,
        external_id,
        base_job_name,
        job_name,
        tags=None
):
    """
    Trains ML model(s) on SageMaker

    :param dir: [str], source root directory
    :param input_s3_dir: [str], S3 location to input data
    :param output_s3_dir: [str], S3 location to save output (models, etc)
    :param hyperparams_file: [str], path to hyperparams json file
    :param ec2_type: [str], ec2 instance type. Refer to:
    https://aws.amazon.com/sagemaker/pricing/instance-types/
    :param volume_size: [int], size in GB of the EBS volume
    :param time_out: [int], time-out in seconds
    :param docker_tag: [str], the Docker tag for the image
    :param aws_role: [str], the AWS role assumed by SageMaker while training
    :param external_id: [str], Optional external id used when using an IAM role
    :param base_job_name: [str], Optional prefix for the SageMaker training job
    :param job_name: [str], Optional name for the SageMaker training job. Overrides `base_job_name`
    :param tags: [optional[list[dict]], default: None], List of tags for labeling a training
        job. For more, see https://docs.aws.amazon.com/sagemaker/latest/dg/API_Tag.html. Example:

        [
            {
                'Key': 'key_name_1',
                'Value': key_value_1,
            },
            {
                'Key': 'key_name_2',
                'Value': key_value_2,
            },
            ...
        ]
    :return: [str], S3 model location
    """
    config = _read_config(dir)
    hyperparams_dict = _read_hyperparams_config(hyperparams_file) if hyperparams_file else None
    sage_maker_client = sagemaker.SageMakerClient(config.aws_profile, config.aws_region, aws_role, external_id)

    image_name = config.image_name+':'+docker_tag

    return sage_maker_client.train(
        image_name=image_name,
        input_s3_data_location=input_s3_dir,
        train_instance_count=1,
        train_instance_type=ec2_type,
        train_volume_size=volume_size,
        train_max_run=time_out,
        output_path=output_s3_dir,
        hyperparameters=hyperparams_dict,
        base_job_name=base_job_name,
        job_name=job_name,
        tags=tags
    )


def deploy(dir, s3_model_location, num_instances, ec2_type, docker_tag, aws_role=None, external_id=None, tags=None):
    """
    Deploys ML model(s) on SageMaker

    :param dir: [str], source root directory
    :param s3_model_location: [str], S3 model location
    :param num_instances: [int], number of ec2 instances
    :param ec2_type: [str], ec2 instance type. Refer to:
    https://aws.amazon.com/sagemaker/pricing/instance-types/
    :param docker_tag: [str], the Docker tag for the image
    :param aws_role: [str], the AWS role assumed by SageMaker while deploying
    :param external_id: [str], Optional external id used when using an IAM role
    :param tags: [optional[list[dict]], default: None], List of tags for labeling a training
        job. For more, see https://docs.aws.amazon.com/sagemaker/latest/dg/API_Tag.html. Example:

        [
            {
                'Key': 'key_name_1',
                'Value': key_value_1,
            },
            {
                'Key': 'key_name_2',
                'Value': key_value_2,
            },
            ...
        ]

    :return: [str], endpoint name
    """
    config = _read_config(dir)
    image_name = config.image_name+':'+docker_tag

    sage_maker_client = sagemaker.SageMakerClient(config.aws_profile, config.aws_region, aws_role, external_id)
    return sage_maker_client.deploy(
        image_name=image_name,
        s3_model_location=s3_model_location,
        train_instance_count=num_instances,
        train_instance_type=ec2_type,
        tags=tags
    )


def batch_transform(
        dir,
        s3_model_location,
        s3_input_location,
        s3_output_location,
        num_instances,
        ec2_type,
        docker_tag,
        aws_role=None,
        external_id=None,
        tags=None
):
    """
    Executes a batch transform job given a trained ML model on SageMaker

    :param dir: [str], source root directory
    :param s3_model_location: [str], S3 model location
    :param s3_input_location: [str], S3 input data location
    :param s3_output_location: [str], S3 location to save predictions
    :param num_instances: [int], number of ec2 instances
    :param ec2_type: [str], ec2 instance type. Refer to:
    https://aws.amazon.com/sagemaker/pricing/instance-types/
    :param docker_tag: [str], the Docker tag for the image
    :param aws_role: [str], the AWS role assumed by SageMaker while deploying
    :param external_id: [str], Optional external id used when using an IAM role
    :param tags: [optional[list[dict]], default: None], List of tags for labeling a training
        job. For more, see https://docs.aws.amazon.com/sagemaker/latest/dg/API_Tag.html. Example:

        [
            {
                'Key': 'key_name_1',
                'Value': key_value_1,
            },
            {
                'Key': 'key_name_2',
                'Value': key_value_2,
            },
            ...
        ]
    """
    config = _read_config(dir)
    image_name = config.image_name + ':' + docker_tag

    sage_maker_client = sagemaker.SageMakerClient(config.aws_profile, config.aws_region, aws_role, external_id)
    sage_maker_client.batch_transform(
        image_name=image_name,
        s3_model_location=s3_model_location,
        s3_input_location=s3_input_location,
        s3_output_location=s3_output_location,
        transform_instance_count=num_instances,
        transform_instance_type=ec2_type,
        tags=tags
    )
