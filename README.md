### pyH2oMojo

#### Unofficial Python wrapper for H2o MOJO's

A lightweight python wrapper around an H2o EasyPredictModelWrapper instance

Instantiating the object will launch the bundled Jar file, and establish a port on localhost on which to communicate with.

Dictionaries or JSON strings are passed to the predictor instance over a socket, and the output is read back via the subprocess' stdout pipe.

#### Usage

```
from pyH2oMojo import H2oMojoPredictor
# pass at minimum, the filename of the MOJO, and the predictor type
predictor = H2oMojoPredictor("my_nn.zip", "multivariate", verbose=True)

print(H2oMojoPredictor.predict({"sepal_length":4.9, "sepal_width":3.0, "petal_length":1.4,"petal_width":0.2}))
>>> {"prediction":"Iris-setosa", "predictionIndex":1, "classProbabilities":[0.0, 0.944, 0.056]}

print(H2oMojoPredictor.supported_predictors())
>>> ["multivariate", "regression", "ordinal", "binomial", "autoencoder", "clustering", "dimreduction"]

# other constructor parameters include:
# x_cols=None # List of columns to be passed to predict() - by default everything is passed
# x_types=None # Dictionary of column name and types ('int', 'real', 'str') - these values will be converted before being sent to the model. 
# connection_timeout=10.0 # Number of seconds to wait for the Java subprocess to start before raising a runtime error
# prediction_timeout=3.0 # Number of seconds to wait for a response from the Java subprocess before raising a runtime error
```