# Annual and Perennial Agriculture Separation - Methodology Description

The methodology here described aims to provide the means to separate annual and perennial agriculture in the previous agriculture mask created, developed in the context of the Brazilian Semiarid region. One aspect that influenced this methodology is the pertinent presence of clouds in some areas, which induced the adoption of time series data. All scripts used in the methodology are presented here with values adapted to be used for the Brazilian Semiarid and builds up from previously generated files, however, changes can easily be done to adapt it to create other Land Use and Land Cover (LULC) maps for other regions. The following text briefly explains concepts adopted, as well as why they were used.

The following table of contents represent the simple steps necessary to create this separation. Please note that as a requirement, the agriculture mask for the study region must be generated.

+ 1. [Samples Creation](#1)
+ 2. [Training LSTM Models](#2)
+ 3. [Creating a Prediction for the Whole Study Area](#3)
+ 4. [Merge All Tiles Created in Prediction Process](#4)

## 1. Samples Creation <a name="1"></a>

Script ```01 - Create Training Samples.ipynb``` was created with the purpose of helping during the process of preparing training samples. The strategy is simple: randomly select points considering a reference contained in a TIF raster file.

The training samples are randomly selected considering the desired amount, then shuffled and also scaled between 0 and 1. In this case, auxiliary files are created to store the necessary parameters for the linear scaling of samples. These are later used to also scale input data during prediction over never seen data.

The script reuses data obtained during the agriculture mask creations step, like the shapefile with tiles delimitation and monthly time series.

## 2. Training LSTM Models <a name="2"></a>

For this step, ```02 - Train LSTM Model.ipynb``` serves as the main script. In this step, a multi-LSTM layers model is created and training with the samples created with the previous script. During this phase, the initial learning-rate, number of epochs, loss function, number of LSTM layers, and more parameters of the model may be chosen. The main library used to implement the model is Tensorflow, so a GPU can be employed to accelerate training.

The script has mechanisms to update plots for loss and accuracy curves during training time, as well as a mechanism to always save the most accurate model considering all previous epochs. The models are saved using ```.h5``` file format, which allows for their later use.

## 3. Creating a Prediction for he Whole Study Area <a name="3"></a>

The main script considered during this step is ```03 - Create Prediction.ipynb```. Here, the most accurate model is used to predict over the monthly time series tiles, creating the separation between annual and perennial agriculture. The script only predicts over pixel time series inside the agriculture mask defined in the previous step, what represents an important optimization procedure.

## 4. Merge All Tiles Created in Prediction Process <a name="4"></a>

For this step, script ```04 - Merging Results.ipynb``` should be used. Since predictions were created according for each tile in the previous operation, one still might need them to be merged into a single file.

More information about each part of this methodology can be found inside each script.