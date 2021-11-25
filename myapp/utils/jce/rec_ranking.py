

from .taf.core import tafcore;
from .taf.__rpc import ServantProxy;


class FeatureData(tafcore.struct):
    __taf_class__ = "recRanking.FeatureData";
    vctcls_float32s = tafcore.vctclass(tafcore.float);
    vctcls_strings = tafcore.vctclass(tafcore.string);
    vctcls_int32s = tafcore.vctclass(tafcore.int32);
    vctcls_int64s = tafcore.vctclass(tafcore.int64);
    vctcls_float64s = tafcore.vctclass(tafcore.double);
    
    def __init__(self):
        self.float32s = FeatureData.vctcls_float32s();
        self.strings = FeatureData.vctcls_strings();
        self.int32s = FeatureData.vctcls_int32s();
        self.int64s = FeatureData.vctcls_int64s();
        self.float64s = FeatureData.vctcls_float64s();
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(value.vctcls_float32s, 0, value.float32s);
        oos.write(value.vctcls_strings, 1, value.strings);
        oos.write(value.vctcls_int32s, 2, value.int32s);
        oos.write(value.vctcls_int64s, 3, value.int64s);
        oos.write(value.vctcls_float64s, 4, value.float64s);
    
    @staticmethod
    def readFrom(ios):
        value = FeatureData();
        value.float32s= ios.read(value.vctcls_float32s, 0, False, value.float32s);
        value.strings= ios.read(value.vctcls_strings, 1, False, value.strings);
        value.int32s= ios.read(value.vctcls_int32s, 2, False, value.int32s);
        value.int64s= ios.read(value.vctcls_int64s, 3, False, value.int64s);
        value.float64s= ios.read(value.vctcls_float64s, 4, False, value.float64s);
        return value;

class FeatureKV(tafcore.struct):
    __taf_class__ = "recRanking.FeatureKV";
    
    def __init__(self):
        self.featureK = "";
        self.featureV = FeatureData();
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(tafcore.string, 0, value.featureK);
        oos.write(FeatureData, 1, value.featureV);
    
    @staticmethod
    def readFrom(ios):
        value = FeatureKV();
        value.featureK= ios.read(tafcore.string, 0, True, value.featureK);
        value.featureV= ios.read(FeatureData, 1, True, value.featureV);
        return value;

class RankingReq(tafcore.struct):
    __taf_class__ = "recRanking.RankingReq";
    mapcls_itemFeatures = tafcore.mapclass(tafcore.int64, tafcore.vctclass(FeatureKV));
    vctcls_userFeatures = tafcore.vctclass(FeatureKV);
    
    def __init__(self):
        self.modelName = "";
        self.itemFeatures = RankingReq.mapcls_itemFeatures();
        self.userFeatures = RankingReq.vctcls_userFeatures();
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(tafcore.string, 0, value.modelName);
        oos.write(value.mapcls_itemFeatures, 1, value.itemFeatures);
        oos.write(value.vctcls_userFeatures, 2, value.userFeatures);
    
    @staticmethod
    def readFrom(ios):
        value = RankingReq();
        value.modelName= ios.read(tafcore.string, 0, True, value.modelName);
        value.itemFeatures= ios.read(value.mapcls_itemFeatures, 1, True, value.itemFeatures);
        value.userFeatures= ios.read(value.vctcls_userFeatures, 2, False, value.userFeatures);
        return value;

class RespKV(tafcore.struct):
    __taf_class__ = "recRanking.RespKV";
    
    def __init__(self):
        self.respK = "";
        self.respV = FeatureData();
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(tafcore.string, 0, value.respK);
        oos.write(FeatureData, 1, value.respV);
    
    @staticmethod
    def readFrom(ios):
        value = RespKV();
        value.respK= ios.read(tafcore.string, 0, True, value.respK);
        value.respV= ios.read(FeatureData, 1, True, value.respV);
        return value;

class Resp(tafcore.struct):
    __taf_class__ = "recRanking.Resp";
    vctcls_respKVs = tafcore.vctclass(RespKV);
    
    def __init__(self):
        self.itemId = 0;
        self.respKVs = Resp.vctcls_respKVs();
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(tafcore.int64, 0, value.itemId);
        oos.write(value.vctcls_respKVs, 1, value.respKVs);
    
    @staticmethod
    def readFrom(ios):
        value = Resp();
        value.itemId= ios.read(tafcore.int64, 0, True, value.itemId);
        value.respKVs= ios.read(value.vctcls_respKVs, 1, True, value.respKVs);
        return value;

class RankingRsp(tafcore.struct):
    __taf_class__ = "recRanking.RankingRsp";
    vctcls_result = tafcore.vctclass(Resp);
    
    def __init__(self):
        self.result = RankingRsp.vctcls_result();
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(value.vctcls_result, 0, value.result);
    
    @staticmethod
    def readFrom(ios):
        value = RankingRsp();
        value.result= ios.read(value.vctcls_result, 0, False, value.result);
        return value;

class RankingFloatReq(tafcore.struct):
    __taf_class__ = "recRanking.RankingFloatReq";
    vctcls_itemFeatures = tafcore.vctclass(tafcore.vctclass(tafcore.float));
    
    def __init__(self):
        self.modelName = "";
        self.itemFeatures = RankingFloatReq.vctcls_itemFeatures();
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(tafcore.string, 0, value.modelName);
        oos.write(value.vctcls_itemFeatures, 1, value.itemFeatures);
    
    @staticmethod
    def readFrom(ios):
        value = RankingFloatReq();
        value.modelName= ios.read(tafcore.string, 0, True, value.modelName);
        value.itemFeatures= ios.read(value.vctcls_itemFeatures, 1, True, value.itemFeatures);
        return value;

class RankingFloatRsp(tafcore.struct):
    __taf_class__ = "recRanking.RankingFloatRsp";
    vctcls_result = tafcore.vctclass(tafcore.vctclass(tafcore.float));
    
    def __init__(self):
        self.result = RankingFloatRsp.vctcls_result();
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(value.vctcls_result, 0, value.result);
    
    @staticmethod
    def readFrom(ios):
        value = RankingFloatRsp();
        value.result= ios.read(value.vctcls_result, 0, False, value.result);
        return value;

class ModelDetailReq(tafcore.struct):
    __taf_class__ = "recRanking.ModelDetailReq";
    
    def __init__(self):
        self.modelName = "";
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(tafcore.string, 0, value.modelName);
    
    @staticmethod
    def readFrom(ios):
        value = ModelDetailReq();
        value.modelName= ios.read(tafcore.string, 0, True, value.modelName);
        return value;

class ModelDetailRsp(tafcore.struct):
    __taf_class__ = "recRanking.ModelDetailRsp";
    vctcls_allVersions = tafcore.vctclass(tafcore.string);
    
    def __init__(self):
        self.modelName = "";
        self.onlineVersion = "";
        self.allVersions = ModelDetailRsp.vctcls_allVersions();
    
    @staticmethod
    def writeTo(oos, value):
        oos.write(tafcore.string, 0, value.modelName);
        oos.write(tafcore.string, 1, value.onlineVersion);
        oos.write(value.vctcls_allVersions, 2, value.allVersions);
    
    @staticmethod
    def readFrom(ios):
        value = ModelDetailRsp();
        value.modelName= ios.read(tafcore.string, 0, True, value.modelName);
        value.onlineVersion= ios.read(tafcore.string, 1, True, value.onlineVersion);
        value.allVersions= ios.read(value.vctcls_allVersions, 2, True, value.allVersions);
        return value;

#proxy for client
class RecRankingSvrProxy(ServantProxy):
    def Predict(self, req, context = ServantProxy.mapcls_context()):
        oos = tafcore.JceOutputStream();
        oos.write(RankingReq, 1, req);

        rsp = self.taf_invoke(ServantProxy.JCENORMAL, "Predict", oos.getBuffer(), context, None);

        ios = tafcore.JceInputStream(rsp.sBuffer);
        ret = ios.read(tafcore.int32, 0, True);
        rsp = ios.read(RankingRsp, 2, True);

        return (ret, rsp);

    def PredictByFloat(self, req, context = ServantProxy.mapcls_context()):
        oos = tafcore.JceOutputStream();
        oos.write(RankingFloatReq, 1, req);

        rsp = self.taf_invoke(ServantProxy.JCENORMAL, "PredictByFloat", oos.getBuffer(), context, None);

        ios = tafcore.JceInputStream(rsp.sBuffer);
        ret = ios.read(tafcore.int32, 0, True);
        rsp = ios.read(RankingFloatRsp, 2, True);

        return (ret, rsp);

    def GetModelDetail(self, req, context = ServantProxy.mapcls_context()):
        oos = tafcore.JceOutputStream();
        oos.write(ModelDetailReq, 1, req);

        rsp = self.taf_invoke(ServantProxy.JCENORMAL, "GetModelDetail", oos.getBuffer(), context, None);

        ios = tafcore.JceInputStream(rsp.sBuffer);
        ret = ios.read(tafcore.int32, 0, True);
        rsp = ios.read(ModelDetailRsp, 2, True);

        return (ret, rsp);




