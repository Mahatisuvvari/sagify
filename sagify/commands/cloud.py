# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json
import os
import sys

import click

from sagify.commands import ASCII_LOGO
from sagify.config.config import ConfigManager
from sagify.log import logger
from sagify.sagemaker import sagemaker


def _read_config(input_dir):
    config_file_path = os.path.join(input_dir, 'sagify', 'config.json')
    if not os.path.isfile(config_file_path):
        logger.info("This is not a sagify directory: {}".format(input_dir))
        sys.exit(-1)

    return ConfigManager(config_file_path).get_config()


def _read_hyperparams_config(hyperparams_file_path):
    if not os.path.isfile(hyperparams_file_path):
        logger.info("The given hyperparams file {} doens't exist".format(hyperparams_file_path))
        sys.exit(-1)

    with open(hyperparams_file_path) as _in_file:
        return json.load(_in_file)


@click.group()
def cloud():
    """
    Commands for AWS operations: upload data, train and deploy
    """
    pass


@click.command(name='upload-data')
@click.option(u"-d", u"--dir", required=False, default='.')
@click.option(u"-i", u"--input-dir", required=True)
@click.option(u"-s", u"--s3-dir", required=True)
def upload_data(dir, input_dir, s3_dir):
    """
    Command to upload data to S3
    """
    logger.info(ASCII_LOGO)
    logger.info("Started uploading data to S3...\n")

    config = _read_config(dir)
    sage_maker_client = sagemaker.SageMakerClient(config.aws_profile, config.aws_region)

    s3_path = sage_maker_client.upload_data(input_dir, s3_dir)

    logger.info("Data uploaded to {} successfully".format(s3_path))


@click.command()
@click.option(u"-d", u"--dir", required=False, default='.')
@click.option(u"-i", u"--input-s3-dir", required=True)
@click.option(u"-o", u"--output-s3-dir", required=True)
@click.option(u"-h", u"--hyperparams-file", required=False)
@click.option(u"-e", u"--ec2-type", required=True)
@click.option(u"-v", u"--volume-size", required=False, default=30)
@click.option(u"-t", u"--time-out", required=False, default=24 * 60 * 60)
def train(dir, input_s3_dir, output_s3_dir, hyperparams_file, ec2_type, volume_size, time_out):
    """
    Command to train ML model(s) on SageMaker
    """
    logger.info(ASCII_LOGO)
    logger.info("Started training on SageMaker...\n")

    config = _read_config(dir)
    hyperparams_dict = _read_hyperparams_config(hyperparams_file) if hyperparams_file else None

    sage_maker_client = sagemaker.SageMakerClient(config.aws_profile, config.aws_region)
    sage_maker_client.train(
        image_name=config.image_name,
        input_s3_data_location=input_s3_dir,
        train_instance_count=1,
        train_instance_type=ec2_type,
        train_volume_size=volume_size,
        train_max_run=time_out,
        output_path=output_s3_dir,
        hyperparameters=hyperparams_dict
    )

    logger.info("Training on SageMaker succeeded")


@click.command()
@click.option(u"-d", u"--dir", required=False, default='.')
@click.option(u"-n", u"--num-instances", required=True)
@click.option(u"-e", u"--ec2-type", required=True)
def deploy(dir, num_instances, ec2_type):
    """
    Command to deploy ML model(s) on SageMaker
    """
    logger.info(ASCII_LOGO)
    logger.info("Started deployment on SageMaker ...\n")


cloud.add_command(upload_data)
cloud.add_command(train)
cloud.add_command(deploy)
