var vm = new Vue({
	el: '#app',
	data: {
		error_name: false,
		error_password: false,
		error_check_password: false,
		error_phone: false,
		error_allow: false,
		error_image_code: false,
		error_sms_code: false,

		username: '',
		password: '',
		password2: '',
		mobile: '', 
		image_code: '',
		sms_code: '',
		allow: false,
		image_code_id:'',
		image_code_url:'',
		sending_flag:'',
        error_image_code_message:'请填写图片验证码',
        sms_code_tip:'获取短信验证码',
	},
	mounted: function(){
		this.generate_image_code();
	},
	methods: {
		//生成uuid
		generate_uuid: function(){
			var d = new Date().getTime();
			if(window.performance && typeof window.performance.now === "function"){
				d += performance.now(); //use high-precision timer if available
			}
			var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
				var r = (d + Math.random()*16)%16 | 0;
				d = Math.floor(d/16);
				return (c =='x' ? r : (r&0x3|0x8)).toString(16);
			});
			return uuid;
    	},
		generate_image_code:function(){
			// 发起请求,请求图片验证码
			this.image_code_id = this.generate_uuid();
			this.image_code_url = "http://127.0.0.1:8000/image_codes/" + this.image_code_id + "/";
		},
		//发送短信验证码
		send_sms_code: function(){
            if(this.sending_flag == true){
                    return;
            }
            this.sending_flag = true;

            this.check_phone();
            this.check_image_code();

            if(this.error_phone == true || this.error_image_code == true){
                this.sending_flag = false;
                return;
            }

            axios.get('http://127.0.0.1:8000/sms_codes/' + this.mobile + '/?text=' + this.image_code + '&image_code_id=' + this.image_code_id,{
                    responseType: 'json'
                })
                .then(response => {
                    var num = 60;
                    var t = setInterval(() =>{
                        if(num == 1){
                            clearInterval(t);
                            this.sms_code_tip = '获取短信验证码';
                            this.sending_flag = false;
                        }else {
                            num -= 1;
                            this.sms_code_tip = num + '秒';
                        }
                    }, 1000, 50)
                })
                .catch(error => {
                    if(error.response.status == 400){
                        this.error_image_code_message  = '图片验证码有误';
                        this.error_image_code = true;
                    }else {
                        console.log(error.response.data);
                    }
                    this.sending_flag = false;
                })
        },
		check_username: function (){
			var len = this.username.length;
			if(len<5||len>20) {
				this.error_name = true;
			} else {
				this.error_name = false;
			}
		},
		check_pwd: function (){
			var len = this.password.length;
			if(len<8||len>20){
				this.error_password = true;
			} else {
				this.error_password = false;
			}		
		},
		check_cpwd: function (){
			if(this.password!=this.password2) {
				this.error_check_password = true;
			} else {
				this.error_check_password = false;
			}		
		},
		check_phone: function (){
			var re = /^1[345789]\d{9}$/;
			if(re.test(this.mobile)) {
				this.error_phone = false;
			} else {
				this.error_phone = true;
			}
		},
		check_image_code: function (){
			if(!this.image_code) {
				this.error_image_code = true;
			} else {
				this.error_image_code = false;
			}	
		},
		check_sms_code: function(){
			if(!this.sms_code){
				this.error_sms_code = true;
			} else {
				this.error_sms_code = false;
			}
		},
		check_allow: function(){
			if(!this.allow) {
				this.error_allow = true;
			} else {
				this.error_allow = false;
			}
		},
		// 注册
		on_submit: function(){
			this.check_username();
			this.check_pwd();
			this.check_cpwd();
			this.check_phone();
			this.check_sms_code();
			this.check_allow();
		}
	}
});
