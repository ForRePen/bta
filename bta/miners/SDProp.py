# This file is part of the BTA toolset
# (c) EADS CERT and EADS Innovation Works

from bta.miners import Miner, ListACE
from pprint import pprint
import re

@Miner.register
class SDProp(Miner):
    _name_ = "SDProp"
    _desc_ = "check integrity of SDHolder and protected account"
    
    @classmethod
    def create_arg_subparser(cls, parser):
        parser.add_argument("--list", action="store_true", help="Find accounts protected by SDHolder")
        parser.add_argument("--orphan", action="store_true", help="Find accounts unlinked from SDHolder")
        parser.add_argument("--checkACE", action="store_true", help="Check ACE replicated by AdminSDHolder")
    
    def list(self):
        user = list()
        group = list()
        t = list()
        for r in self.datatable.find({"adminCount":{"$exists": True, "$ne":0}}):
            if r["objectCategory"] == self.categories.person:
                user.append([r["cn"], 'User', r["objectSid"]])
            elif r["objectCategory"] == self.categories.group:
                group.append([r["cn"], 'Group', r["objectSid"]])
            else:
                print '***** Unknown category (%d) for %s' % (r["objectCategory"], r["objectSid"])
        user.sort(key=lambda x: x[0].lower())
        group.sort(key=lambda x: x[0].lower())
        for g in group:
            t.append(g)
        for u in user:
            t.append(u)
        t.insert(0, [])
        t.insert(0, ["cn","type","SID"])
        return t
        
    def orphanSD(self):
        user = list()
        group = list()
        t = list()
        for r in self.datatable.find({"adminCount":{"$exists": True, "$ne":1}}):
            if r["objectCategory"] == self.categories.person:
                user.append([r["cn"], 'User', r["objectSid"]])
            elif r["objectCategory"] == self.categories.person:
                group.append([r["cn"], 'Group', r["objectSid"]])
            else:
                print '***** Unknown category (%d) for %s' % (r["objectCategory"], r["objectSid"])
        user.sort(key=lambda x: x[0].lower())
        group.sort(key=lambda x: x[0].lower())
        for g in group:
            t.append(g)
        for u in user:
            t.append(u)
        t.insert(0, [])
        t.insert(0, ["cn","type","SID"])
        return t
        
    def checkACE(self):
        secDesc = int(self.datatable.find_one({"cn": "AdminSDHolder"})['nTSecurityDescriptor'])
        hdlACE = ListACE.ListACE(self.backend)
        securitydescriptor = hdlACE.getSecurityDescriptor(secDesc)
        aceList = hdlACE.extractACE(securitydescriptor)
        
        t = list()
        for ace in aceList:
            name = self.datatable.find_one({"objectSid": ace['SID']}, {"cn"})['cn']
            if ace['InheritedObjectType'] != None:
                cible = self.datatable.find_one({"schemaIDGUID" : re.compile(ace['InheritedObjectType'], re.IGNORECASE)})
                if cible == None: 
                    cible = self.datatable.find_one({"rightsGuid" : re.compile(ace['InheritedObjectType'], re.IGNORECASE)})
                cible = cible['cn']
            elif ace['ObjectType'] != None:
                cible = self.datatable.find_one({"schemaIDGUID" : re.compile(ace['ObjectType'], re.IGNORECASE)})
                if cible == None: 
                    cible = self.datatable.find_one({"rightsGuid" : re.compile(ace['ObjectType'], re.IGNORECASE)})
                cible = cible['cn']
            else:
                cible = 'ALL'
            t.append([name, ace['Type'], cible])
        t.sort(key=lambda x: x[0].lower())
        t.insert(0, [])
        t.insert(0, ["cn","type","SID"])
        return t

    def run(self, options, doc):
        if options.list:
            toDisplay = self.list()
            t = doc.create_table("Account protected by SDHolder")
            for disp in toDisplay:
                t.add(disp)
            t.flush()
            t.finished()
        elif options.orphan:
            toDisplay = self.orphanSD()
            t = doc.create_table("Accounts unlinked from SDHolder")
            for disp in toDisplay:
                t.add(disp)
            t.flush()
            t.finished()
        elif options.checkACE:
            toDisplay = self.checkACE()
            t = doc.create_table("Rigts replicated by SDHolder on protected account")
            for disp in toDisplay:
                t.add(disp)
            t.flush()
            t.finished()
            
    def assert_consistency(self):
        Miner.assert_consistency(self)
        self.assert_field_type(self.datatable, "adminCount", int)
        self.assert_field_exists(self.datatable, "objectSid")
        self.assert_field_exists(self.datatable, "objectCategory")
        self.assert_field_type(self.datatable, "objectCategory", int)
        self.assert_field_exists(self.datatable, "cn")
        self.assert_field_type(self.datatable, "InheritedObjectType", str, unicode)
        self.assert_field_type(self.datatable, "schemaIDGUID", str, unicode)
        self.assert_field_type(self.datatable, "rightsGuid", str, unicode)