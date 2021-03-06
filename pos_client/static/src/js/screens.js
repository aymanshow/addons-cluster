function pos_client_screens(instance,module){
       
    module.PaymentScreenWidget.include({
        
        showCustomerPopup:function(){
            popup = new module.Alert(this, {title:"Error",msg:"Please select a customer"});
            popup.appendTo($('.point-of-sale'));
        },        
        validateCurrentOrder : function(){
            currentOrder = this.pos.get('selectedOrder');
            if(currentOrder.get_client()!= null)
                this._super();
            else{
                this.showCustomerPopup();
            }                
        }        
    })
    
    module.CustomerBasePopup = module.PopUpWidget.extend({
        template:"CustomerBasePopup",
        renderElement:function(){
            this._super();
            this.$("a.close").off('click').click(_.bind(this.closePopup,this))
        },
        closePopup:function(e){
            this.close();
            this.hide();
        },        
    });   
            
    module.CustomerForm = module.BasePopup.extend({
        template:'CustomerForm',
        events:{
            "click button[name='save']":"onClickBtnSave",
            "click button[name='cancel']":"onClickBtnCancel",
            "click button[name='search']":"onClickBtnSearch",
            "change input[type='text']": "onChangeTextbox",
            "change input[type='radio']":"onChangeRadio",
            "change input[name='vat_subjected']":"onChangeVatSubjected",
            "change input[name='wh_iva_agent']":"onChangeWhIvaAgent",  
            "keypress input[name='vat']":"onKeypressVat", 
            "keypress input[name='street']":"onKeypressStreet",
            "keypress input[name='street2']":"onKeypressStreet2",
            "keypress input[name='city']":"onKeypressCity",
            "keypress input[name='phone']":"onKeypressPhone", 
            "keypress input[name='email']":"onKeypressEmail",                
        },       
        init: function(parent, options){
            this._super(parent, options);
            this.id = "customer-form";
            this.customer = new module.Customer();
            this.operation = "Create"; 
        }, 
        show: function(){
            self = this;
            this._super(); 
            this.seniat_url = new instance.web.Model('seniat.url');
            this.build_ui();
            this.disable_controls();
            this.initialize(); 
        },        
        build_ui: function(){
            self = this;             
            $("#choiceType").buttonset();           
            $("#customer-form").position({my:"center",of:".point-of-sale"});
            $(".popup").draggable();
        },
        renderElement: function(){
            ids = $('input:disabled')
            this._super();
            this.build_ui();
            $(ids).each(function(index,value){
                $("input[name='"+value.name+"']").attr("disabled","disabled");               
            });           
        },
        setOperation:function(value){
            this.operation = value;
            this.renderElement();
        },
        initialize:function(){
            this.operation = "Create";                  
            this.customer = new module.Customer();
            this.customer.setVatLetter(this.$(":radio:first").val()); 
            this.renderElement();
            this.$("input[name='vat']").focus()
        },
        customer_search: function(vat){
            var id = this.pos.db.search_customer(vat);
            return id;
        },
        ask_for_update:function(){
            var self = this
            c = new module.Confirm(this, {title:"Question",msg:"This customer already exists. Do you want to upgrade it?"});
            c.appendTo($('.point-of-sale'));
            c.on('yes',this,function(){
                vat = self.customer.get('vat');
                self.seniat_request(vat);
                self.setOperation("Update");
                self.$("input[name='street']").focus();
            });
            c.on('no',this,function(){
                self.setOperation("Select");
                self.$("button[name='save']").focus()
            });  
        },
        load_customer:function(c){
            this.load_data(c);
            this.ask_for_update();            
        },
        load_data:function(c){          
            this.customer.set({
                'id':c.id,
                'name':c.name || "",
                'vat_subjected':c.vat_subjected,
                'wh_iva_agent':c.wh_iva_agent,
                'street':c.street || "",
                'street':c.street || "",
                'street2':c.street2 || "",
                'city':c.city || "",
                'phone':c.phone || "",
                'email':c.email || "",
            });                
            this.renderElement();
        },
        load_data_seniat:function(c){
            this.customer.set("seniat_updated",true);
            this.customer.set("name",c.name);          
            this.customer.set("wh_iva_agent",c.wh_iva_agent);
            if (this.customer.getVatLetter() != "V")
                this.customer.set("vat_subjected",c.vat_subjected);
            this.renderElement();
        },
        not_found_seniat:function(title,mesg){
            var self = this
            var msg = _.rest(mesg,10).join('') + ". Do you want to continue?";
            c = new module.Confirm(this, {title:title,msg:msg});
            c.appendTo($('.point-of-sale'));
            c.on('yes',this,function(){
                self.enable_controls();
                self.$("input[name='name']").focus();
                self.customer.set('seniat_updated',false);
            });
            c.on('no',this,function(){
                self.$("input[name='vat']").focus();
                self.disable_controls();
            }); 
        },
        seniat_request:function(vat){
            self = this
            this.disable_buttons();
            this.seniat_url.call('check_rif',[vat]).then(function(customer){
                if (customer){
                    self.load_data_seniat(customer);
                    self.enable_controls();
                    self.$("input[name='street']").focus();
                } 
                self.enable_buttons();               
            }).fail(function(obj, event){
                event.preventDefault();
                self.not_found_seniat(obj.message,obj.data.fault_code);
                self.enable_buttons();
            })
                
        },
        validateFields:function(){
            if (this.customer.get('vat') == undefined){
                this.show_popup("Error","The field 'vat' is required","input[name='vat']");
                return false;
            }else if (this.customer.get('name')==undefined){
                this.show_popup("Error","The field 'name' is required","input[name='name']");
                return false;
            }else if (this.customer.get('street')==undefined){
                this.show_popup("Error","The field 'street' is required","input[name='street']");
                return false;
            }else if (this.customer.get('city')==undefined){
                this.show_popup("Error","The field 'city' is required","input[name='city']");
                return false;
            }else if (this.customer.get('phone')==undefined){
                this.show_popup("Error","The field 'phone' is required","input[name='phone']");
                return false;
            }
            return true;
        },
        saveCustomer:function(){
            if (this.operation == "Create")
                this.createCustomer();
            else if (this.operation == "Update")
                this.updateCustomer();
            else
                this.selectCustomer();
        },
        createCustomer:function(){    
            this.pos.create_customer(this.customer.toJSON()); 
            this.show_popup("Notification","Customer successfully created");
            this.selectCustomer();
        },
        updateCustomer:function(){
            if (this.customer.hasChanged()){
                c = this.customer.changedAttributes();
                c.id = this.customer.get('id');
                c.vat = this.customer.get('vat');
                console.debug(c);                 
                this.pos.update_customer(c);
                this.show_popup("Notification","Customer successfully update");           
            }
            this.selectCustomer();
        },
        selectCustomer:function(){
            this.pos.get('selectedOrder').set_client(this.customer.toJSON());
            this.pos.set('client',this.customer.toJSON());
            this.onClickBtnCancel()
            this.close();
            this.hide(); 
        },
        show_popup: function(title,msg,el){
            alert = new module.Alert(this, {title:title,msg:msg});
            alert.appendTo($('.point-of-sale'));
        },    
        disable_controls : function(){              
            this.$("input[type=text]").attr("disabled","disabled");
            this.$(":checkbox").attr("disabled","disabled");
            this.$("input[name='vat']").removeAttr("disabled");
            this.$("button[name='search']").removeAttr("disabled","disabled"); 
            this.$(":radio").removeAttr("disabled");                             
        },
        enable_controls : function(){          
            this.$("input[type=text]").removeAttr("disabled");
            this.$(":checkbox").removeAttr("disabled");
            this.$(":radio").attr("disabled","disabled");   
            this.$("input[name='vat']").attr("disabled","disabled");
            this.$("button[name='search']").attr("disabled","disabled");                 
        },
        enable_buttons:function(){
            this.$(":button").removeAttr("disabled");
        },
        disable_buttons:function(){
            this.$(":button").attr("disabled","disabled");
        },      
        onClickBtnSave:function(){
            if (this.validateFields())
                this.saveCustomer();
        }, 
        onClickBtnSearch: function(){
            vat = this.customer.get('vat');
            regex = new RegExp(/^[A-Z]{2}[VE]?([0-9]){1,9}$|^[A-Z]{2}[JGP]?([0-9]){9}$/);
            if (regex.test(vat)){
                c = this.customer_search(vat)
                if (c != null)
                    this.load_customer(c);
                else
                    this.seniat_request(vat);
            }else{
                this.show_popup("Error","This VAT number does not seem to be valid!");
            }           
        }, 
        onClickBtnCancel: function(){
            this.initialize();
            this.disable_controls();
        },    
        onChangeTextbox:function(e){
            name = e.target.name;
            value = e.target.value;
            if (name != "vat")
                this.customer.set(name,value);
            else
                this.customer.setVatNumbers(value);
        },
        onChangeRadio:function(e){
            this.customer.setVatLetter(e.target.value);
            this.$("input[name='vat']").focus();;
        },
        onChangeVatSubjected:function(e){
            if (this.$(e.target).attr('checked'))
                this.customer.set('vat_subjected',true);
            else
                this.customer.set('vat_subjected',false);
        },  
        onChangeWhIvaAgent:function(e){
            if (this.$(e.target).attr('checked'))
                this.customer.set('wh_iva_agent',true)
            else
                this.customer.set('wh_iva_agent',false)
        },  
        onKeypressVat:function(e){
            if (e.which == '13'){
                this.customer.setVatNumbers(e.target.value);
                this.$("button[name='search']").trigger('click');
                e.preventDefault();
            }
        },
        onKeypressStreet:function(e){            
            if (e.which == '13'){
                this.$("input[name='street2']").focus();
                e.preventDefault();
            }
        }, 
        onKeypressStreet2:function(e){            
            if (e.which == '13'){
                this.$("input[name='city']").focus();
                e.preventDefault();
            }
        }, 
        onKeypressCity:function(e){            
            if (e.which == '13'){
                this.$("input[name='phone']").focus();
                e.preventDefault();
            }
        },
        onKeypressPhone:function(e){            
            if (e.which == '13'){
                this.$("input[name='email']").focus();
                e.preventDefault();
            }
        },
        onKeypressEmail:function(e){            
            if (e.which == '13'){
                this.$("button[name='save']").focus();
                e.preventDefault();
            }
        },
        
        
    })
}

