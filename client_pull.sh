#!/usr/bin/env bash

cd $1
git reset --hard
git fetch --all
git checkout $2
