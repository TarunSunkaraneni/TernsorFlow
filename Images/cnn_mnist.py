from __future__ import absolute_import
from __future__ import division
from __future__ import print_function 

#Imports
import numpy as np 
import tensorflow as tf

# {'accuracy': 0.96969998, 'loss': 0.10314358, 'global_step': 20000}

# Convolutional neural networks (CNNs) are the current state-of-the-art model architecture for image classification tasks. 
# CNNs apply a series of filters to the raw pixel data of an image to extract and learn higher-level features, 
# which the model can then use for classification. CNNs contains three components:

# Convolutional layers, which apply a specified number of convolution filters to the image. For each subregion, 
# the layer performs a set of mathematical operations to produce a single value in the output feature map. 
# Convolutional layers then typically apply a ReLU activation function to the output to introduce nonlinearities into the model.


# Pooling layers, which downsample the image data extracted by the convolutional layers to reduce the dimensionality of the feature map
# in order to decrease processing time. A commonly used pooling algorithm is max pooling, which extracts subregions of the feature map 
# (e.g., 2x2-pixel tiles), keeps their maximum value, and discards all other values.

# Dense (fully connected) layers, which perform classification on the features extracted by the convolutional layers 
# and downsampled by the pooling layers. In a dense layer, every node in the layer is connected to every node in the preceding layer.


# Typically, a CNN is composed of a stack of convolutional modules that perform feature extraction. Each module consists of a convolutional layer
# followed by a pooling layer. The last convolutional module is followed by one or more dense layers that perform classification.
# The final dense layer in a CNN contains a single node for each target class in the model (all the possible classes the model may predict),
# with a softmax activation function to generate a value between 0–1 for each node (the sum of all these softmax values is equal to 1).
# We can interpret the softmax values for a given image as relative measurements of how likely it is that the image falls into each target class.
tf.logging.set_verbosity(tf.logging.INFO)

# Our Application logic
def cnn_model_fn(features, labels, mode):
    """ Model funtion for CNN. """
    # Input layer #1
    # Reshape X to 4-D tensor: [batch_size, width, height, channels]
    # MINST images are 28x28 pizels, have one color channel
    input_layer = tf.reshape(features["x"], [-1,28,28,1]) # Batch size, image_height, image_width, channels (monochrome=1)
    
    # Convolutional Layer #1
    # COmputes 32 features using a 5x5 filter with ReLU activation.
    # Padding is added to preserve width and height
    # Input Tensor Shape: [batch_size, 28,28, 1]
    # Output Tensor Shape: [batch_size, 28, 28, 32]
    conv1 = tf.layers.conv2d (
            inputs=input_layer,
            filters=32,
            kernel_size=[5,5],
            padding="same",
            activation=tf.nn.relu)
    
    # Pooling Layer #1
    # First max pooling layer with a 2x2 filter and stride of 2
    # Input Tensor Shape: [batch_size, 28,28,32]
    # Output Tensor Shape: [batch_size, 14, 14, 632]
    pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2,2], strides=2)
    
    # Convolutional Layer #2
    # Computes 64 features using a 5x5 filter. 
    # Padding is added to preserve width and height.
    # Input Tensor Shape: [batch_size, 14, 14, 32]
    # Output Tensor Shape: [batch_size, 14, 14, 64]
    conv2 = tf.layers.conv2d (
            inputs=pool1,
            filters=64,
            kernel_size=[5,5],
            padding="same",
            activation=tf.nn.relu)

    #Poolin Layer #2
    # Second max pooling layer with a 2x2 filter and stride of 2
    # Input Tensor Shape: [batch_size, 14, 14, 64]
    # Output Tensor Shape: [batch_size, 7, 7, 64]
    pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2,2], strides=2)
    
    # Flatten tensor into a batch of vectors
    # Input Tensor Shape: [batch_size, 7, 7, 64]
    # Output Tensor Shape: [batch_size, 7 * 7 * 64]
    pool2_flat = tf.reshape(pool2, [-1,7 * 7 * 64])
    
    # Dense Layer 
    # Densely connected layer with 1024 neurons
    # Input Tensor Shape: [batch_size, 7 * 7 * 64]
    # Output Tensor Shape: [batch_size, 1024]
    dense = tf.layers.dense(inputs=pool2_flat, units=1024, activation=tf.nn.relu)
    
    # Add dropout operation; 0.6 probability that element will be kept
    dropout = tf.layers.dropout(
            inputs=dense, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)
    
    # Logits Layer
    logits = tf.layers.dense(inputs=dropout,units=10)
    
    predictions = {
        #Generate predictions (for PREDICT and EVAL mode)
        "classes": tf.argmax(input=logits,axis=1),
        # Add `softmax_tensor` to the graph. It is used for PREDICT and by the
        # `logging_hook`
        "probabilities": tf.nn.softmax(logits, name="softmax_tensor")}
    
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)
    
    # Calculate Loss (for both TRAIN and EVAL modes)
    loss = tf.losses.sparse_softmax_cross_entropy(labels=labels, logits=logits)

    # Configuring the Training Op (for TRAIN mode)
    if mode == tf.estimator.ModeKeys.TRAIN:
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.001)
        train_op = optimizer.minimize(
                loss=loss,
                global_step=tf.train.get_global_step())
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op)
    
    # Add evaluation metrics (for EVAL mode)
    eval_metric_ops = {
            "accuracy": tf.metrics.accuracy (
                    labels=labels, predictions=predictions["classes"])}
    return tf.estimator.EstimatorSpec(
            mode=mode, loss=loss, eval_metric_ops=eval_metric_ops)  
###################################################################################

def main(arg):
        # Load training and eval data
        mnist = tf.contrib.learn.datasets.load_dataset("mnist")
        train_data=mnist.train.images # np.array
        train_labels = np.asarray(mnist.train.labels, dtype=np.int32)
        eval_data = mnist.test.images # np.array
        eval_labels=np.asarray(mnist.test.labels, dtype=np.int32)
        
        # Create the Estimator
        mnist_classifier = tf.estimator.Estimator(
                model_fn= cnn_model_fn, model_dir="/tmp/mnist_convnet_model")

        # Set up logging for predictions
        # Log the values in the "Softmax" tensor with the label "probabilities"
        tensors_to_log = {"probabilities": "softmax_tensor"}
        logging_hook = tf.train.LoggingTensorHook(
                tensors=tensors_to_log, every_n_iter=50
        )

        # Train the model
        train_input_fn = tf.estimator.inputs.numpy_input_fn(
                x={"x": train_data},
                y=train_labels,
                batch_size=100,
                num_epochs=None,
                shuffle=True
        )
        mnist_classifier.train(
                input_fn=train_input_fn,
                steps=20000,
                hooks=[logging_hook])

        # evaluate the model and print results
        eval_input_fn = tf.estimator.inputs.numpy_input_fn(
                x={"x": eval_data},
                y=eval_labels,
                num_epochs=1,
                shuffle=False)
        eval_results = mnist_classifier.evaluate(input_fn=eval_input_fn)
        print(eval_results)


if __name__ == "__main__":
    tf.app.run()