var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
		hots: [],
		sku_id: sku_id,
        sku_count: 1,
        sku_price: price,
        sku_amount: 0,
        category_id: category_id,
        tab_content: {
		    detail: true,
            pack: false,
            comment: false,
            service: false
        },
        comments: [],
        score_classes: {
            1: 'stars_1',
            2: 'stars_2',
            3: 'stars_3',
            4: 'stars_4',
            5: 'stars_5',
        },
        cart_total_count: 0, // 购物车总数量
        carts: [], // 购物车数据,
    },
    mounted(){
		// 获取热销商品数据
        this.get_hot_goods();

        // 保存用户浏览记录
		this.save_browse_histories();

        // 记录商品详情的访问量
		this.detail_visit();

		// 获取购物车数据
        this.get_carts();

		// 获取商品评价信息
        this.get_goods_comment();
    },
    watch: {
        // 监听商品数量的变化
        sku_count: {
            handler(newValue){
                this.sku_amount = (newValue * this.sku_price).toFixed(2);
            },
            immediate: true
        }
    },
    methods: {
        // 加数量
        on_addition(){
            if (this.sku_count < 5) {
                this.sku_count++;
            } else {
                this.sku_count = 5;
                alert('超过商品数量上限');
            }
            // this.sku_amount = (this.sku_count * this.sku_price).toFixed(2);
        },
        // 减数量
        on_minus(){
            if (this.sku_count > 1) {
                this.sku_count--;
            }
            // this.sku_amount = (this.sku_count * this.sku_price).toFixed(2);
        },
        // 编辑商品数量
        check_sku_count(){
            if (this.sku_count > 5) {
                this.sku_count = 5;
            }
            if (this.sku_count < 1) {
                this.sku_count = 1;
            }
            this.sku_amount = (this.sku_count * this.sku_price).toFixed(2);
        },
        // 控制页面标签页展示
        on_tab_content(name){
            this.tab_content = {
                detail: false,
                pack: false,
                comment: false,
                service: false
            };
            this.tab_content[name] = true;
        },
    	// 获取热销商品数据
        get_hot_goods(){
        	var url = this.hots + '/hot/'+ this.category_id +'/';
            axios.get(url, {
                    responseType: 'json'
                })
                .then(response => {
                    this.hots = response.data.hot_skus;
                    for(var i=0; i<this.hots.length; i++){
                        this.hots[i].url = '/goods/' + this.hots[i].id + '.html';
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
		// 保存用户浏览记录
		save_browse_histories(){
        	if (this.sku_id) {
        		var url = this.host + '/browse_histories/';
				axios.post(url, {
						'sku_id':this.sku_id
					}, {
						headers: {
							'X-CSRFToken':getCookie('csrftoken')
						},
						responseType: 'json'
					})
					.then(response => {
						console.log(response.data);
					})
					.catch(error => {
						console.log(error.response);
					});
			}
		},
		// 记录商品详情的访问量
		detail_visit(){
        	if (this.category_id) {
        		var url = this.hots + '/visit/' + this.category_id + '/';
				axios.post(url, {}, {
						headers: {
							'X-CSRFToken':getCookie('csrftoken')
						},
						responseType: 'json'
					})
					.then(response => {
						console.log(response.data);
					})
					.catch(error => {
						console.log(error.response);
					});
			}
		},
        // 加入购物车
        add_cart(){
            var url = this.host + '/carts/';
            axios.post(url, {
                    sku_id: parseInt(this.sku_id),
                    count: this.sku_count
                }, {
                    headers: {
                        'X-CSRFToken':getCookie('csrftoken')
                    },
                    responseType: 'json',
                    withCredentials: true
                })
                .then(response => {
                    if (response.data.code == '0') {
                        alert('添加购物车成功');
                        this.cart_total_count += this.sku_count;
                        this.get_carts();
                    } else { // 参数错误
                        alert(response.data.errmsg);
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
        // 获取购物车数据
        get_carts(){
        	var url = this.host + '/carts/simple/';
            axios.get(url, {
                    responseType: 'json',
                })
                .then(response => {
                    this.carts = response.data.cart_skus;
                    this.cart_total_count = 0;
                    for(var i=0;i<this.carts.length;i++){
                        if (this.carts[i].name.length>25){
                            this.carts[i].name = this.carts[i].name.substring(0, 25) + '...';
                        }
                        this.cart_total_count += this.carts[i].count;
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
        // 获取商品评价信息
        get_goods_comment(){
            if (this.sku_id) {
                var url = this.hots + '/comments/'+ this.sku_id +'/';
                axios.get(url, {
                        responseType: 'json'
                    })
                    .then(response => {
                        this.comments = response.data.comment_list;
                        for(var i=0; i<this.comments.length; i++){
                            this.comments[i].score_class = this.score_classes[this.comments[i].score];
                        }
                    })
                    .catch(error => {
                        console.log(error.response);
                    });
            }
        },
    }
});
