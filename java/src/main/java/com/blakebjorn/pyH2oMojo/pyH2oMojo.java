package com.blakebjorn.pyH2oMojo;

import hex.genmodel.MojoModel;
import hex.genmodel.easy.EasyPredictModelWrapper;
import hex.genmodel.easy.RowData;
import hex.genmodel.easy.prediction.*;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.util.Arrays;
import java.util.Iterator;


public class pyH2oMojo {

    public static DatagramSocket connect_to_socket(){
        DatagramSocket socketListener;
        int port = 54322;
        while (true) {
            try {
                socketListener = new DatagramSocket(port);
                System.out.println("{\"port\":"+port+"}");
                return socketListener;
            } catch (java.net.SocketException e) {
                port++;
            }
        }
    }

    public static void main(String[] args) throws Exception {
        String modelname = args[0];
        String type = args[1];

        EasyPredictModelWrapper model = new EasyPredictModelWrapper(MojoModel.load(modelname));
        JSONParser parser = new JSONParser();
        DatagramSocket socketListener = connect_to_socket();

        byte[] receiveData = new byte[65000];

        DatagramPacket receivePacket = new DatagramPacket(receiveData, receiveData.length);

        MultinomialModelPrediction u;
        RegressionModelPrediction p;
        JSONObject outObj = new JSONObject();
        String sentence;
        Object obj;
        JSONObject inpObj;
        RowData row = new RowData();

        while (true) {
            socketListener.receive(receivePacket);
            sentence = new String(receivePacket.getData(), 0, receivePacket.getLength());

            obj = parser.parse(sentence);
            inpObj = (JSONObject) obj;
            if (inpObj.containsKey("_command") && inpObj.get("_command") == "exit") {
                break;
            }

            row.clear();
            for (Iterator iterator = inpObj.keySet().iterator(); iterator.hasNext(); ) {
                String key = (String) iterator.next();
                row.put(key, inpObj.get(key));
            }

            if (type.equals("multivariate")) {
                u = model.predictMultinomial(row);
                outObj.put("prediction", u.label);
                outObj.put("predictionIndex", u.labelIndex);
                outObj.put("classProbabilities", Arrays.toString(u.classProbabilities));
            }
            else if (type.equals("regression")) {
                p = model.predictRegression(row);
                outObj.put("prediction", p.value);

            }
            else if (type.equals("ordinal")) {
                OrdinalModelPrediction o = model.predictOrdinal(row);
                outObj.put("prediction", o.label);
                outObj.put("predictionIndex", o.labelIndex);
                outObj.put("classProbabilities", Arrays.toString(o.classProbabilities));
            }
            else if (type.equals("binomial")) {
                BinomialModelPrediction b = model.predictBinomial(row);
                outObj.put("prediction", b.label);
                outObj.put("predictionIndex", b.labelIndex);
                outObj.put("classProbabilities", Arrays.toString(b.classProbabilities));
                outObj.put("calibratedClassProbabilities", Arrays.toString(b.calibratedClassProbabilities));
            }
            else if (type.equals("autoencoder")) {
                AutoEncoderModelPrediction a = model.predictAutoEncoder(row);
                outObj.put("original", a.original);
                outObj.put("reconstructed", a.reconstructed);
                outObj.put("reconstructedRowData", a.reconstructedRowData.toString());
            }
            else if (type.equals("clustering")) {
                ClusteringModelPrediction c = model.predictClustering(row);
                outObj.put("cluster", c.cluster);
                outObj.put("distances", Arrays.toString(c.distances));
            }
            else if (type.equals("dimreduction")) {
                DimReductionModelPrediction d = model.predictDimReduction(row);
                outObj.put("dimensions", d.dimensions);
            }
            System.out.println(outObj);
            outObj.clear();
        }
    }
}