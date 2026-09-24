"""
Indian Cities Database
======================
Real GPS coordinates for major cities across India.
Data used with Open-Meteo for live environmental readings.

Format: (name, city, state, description, latitude, longitude)
"""

INDIAN_CITIES = [
    # ── Maharashtra ──
    ('Mumbai', 'Mumbai', 'Maharashtra', 'Financial capital of India', 19.0760, 72.8777),
    ('Pune', 'Pune', 'Maharashtra', 'Oxford of the East', 18.5204, 73.8567),
    ('Nagpur', 'Nagpur', 'Maharashtra', 'Orange City', 21.1458, 79.0882),
    ('Nashik', 'Nashik', 'Maharashtra', 'Wine capital of India', 19.9975, 73.7898),
    ('Thane', 'Thane', 'Maharashtra', 'City of Lakes', 19.2183, 72.9781),
    ('Aurangabad', 'Aurangabad', 'Maharashtra', 'Tourism hub', 19.8762, 75.3433),
    ('Solapur', 'Solapur', 'Maharashtra', 'Textile city', 17.6599, 75.9064),
    # ── Delhi NCR ──
    ('New Delhi', 'New Delhi', 'Delhi', 'National capital', 28.6139, 77.2090),
    ('Noida', 'Noida', 'Uttar Pradesh', 'NCR satellite city', 28.5355, 77.3910),
    ('Gurugram', 'Gurugram', 'Haryana', 'Millennium City', 28.4595, 77.0266),
    ('Faridabad', 'Faridabad', 'Haryana', 'Industrial hub NCR', 28.4089, 77.3178),
    ('Ghaziabad', 'Ghaziabad', 'Uttar Pradesh', 'Gateway of UP', 28.6692, 77.4538),
    # ── Karnataka ──
    ('Bengaluru', 'Bengaluru', 'Karnataka', 'Silicon Valley of India', 12.9716, 77.5946),
    ('Mysuru', 'Mysuru', 'Karnataka', 'City of Palaces', 12.2958, 76.6394),
    ('Mangaluru', 'Mangaluru', 'Karnataka', 'Port city', 12.9141, 74.8560),
    ('Hubballi', 'Hubballi', 'Karnataka', 'Commercial centre', 15.3647, 75.1240),
    # ── Tamil Nadu ──
    ('Chennai', 'Chennai', 'Tamil Nadu', 'Detroit of India', 13.0827, 80.2707),
    ('Coimbatore', 'Coimbatore', 'Tamil Nadu', 'Manchester of South India', 11.0168, 76.9558),
    ('Madurai', 'Madurai', 'Tamil Nadu', 'Temple city', 9.9252, 78.1198),
    ('Tiruchirappalli', 'Tiruchirappalli', 'Tamil Nadu', 'Rock Fort city', 10.7905, 78.7047),
    ('Salem', 'Salem', 'Tamil Nadu', 'Steel city', 11.6643, 78.1460),
    # ── Telangana ──
    ('Hyderabad', 'Hyderabad', 'Telangana', 'City of Pearls', 17.3850, 78.4867),
    ('Warangal', 'Warangal', 'Telangana', 'Historical city', 17.9784, 79.6000),
    ('Nizamabad', 'Nizamabad', 'Telangana', 'Agricultural hub', 18.6725, 78.0941),
    # ── West Bengal ──
    ('Kolkata', 'Kolkata', 'West Bengal', 'City of Joy', 22.5726, 88.3639),
    ('Howrah', 'Howrah', 'West Bengal', 'Industrial city', 22.5958, 88.2636),
    ('Siliguri', 'Siliguri', 'West Bengal', 'Gateway to Northeast', 26.7271, 88.3953),
    ('Durgapur', 'Durgapur', 'West Bengal', 'Steel city', 23.5204, 87.3119),
    # ── Gujarat ──
    ('Ahmedabad', 'Ahmedabad', 'Gujarat', 'Manchester of India', 23.0225, 72.5714),
    ('Surat', 'Surat', 'Gujarat', 'Diamond city', 21.1702, 72.8311),
    ('Vadodara', 'Vadodara', 'Gujarat', 'Cultural capital of Gujarat', 22.3072, 73.1812),
    ('Rajkot', 'Rajkot', 'Gujarat', 'Commercial hub', 22.3039, 70.8022),
    ('Bhavnagar', 'Bhavnagar', 'Gujarat', 'Port city', 21.7645, 72.1519),
    # ── Rajasthan ──
    ('Jaipur', 'Jaipur', 'Rajasthan', 'Pink City', 26.9124, 75.7873),
    ('Jodhpur', 'Jodhpur', 'Rajasthan', 'Blue City', 26.2389, 73.0243),
    ('Udaipur', 'Udaipur', 'Rajasthan', 'City of Lakes', 24.5854, 73.7125),
    ('Kota', 'Kota', 'Rajasthan', 'Education hub', 25.2138, 75.8648),
    ('Ajmer', 'Ajmer', 'Rajasthan', 'Pilgrimage city', 26.4499, 74.6399),
    # ── Uttar Pradesh ──
    ('Lucknow', 'Lucknow', 'Uttar Pradesh', 'City of Nawabs', 26.8467, 80.9462),
    ('Kanpur', 'Kanpur', 'Uttar Pradesh', 'Leather city', 26.4499, 80.3319),
    ('Varanasi', 'Varanasi', 'Uttar Pradesh', 'Spiritual capital', 25.3176, 82.9739),
    ('Agra', 'Agra', 'Uttar Pradesh', 'City of Taj Mahal', 27.1767, 78.0081),
    ('Meerut', 'Meerut', 'Uttar Pradesh', 'Sports goods hub', 28.9845, 77.7064),
    ('Prayagraj', 'Prayagraj', 'Uttar Pradesh', 'City of confluence', 25.4358, 81.8463),
    # ── Madhya Pradesh ──
    ('Bhopal', 'Bhopal', 'Madhya Pradesh', 'City of Lakes', 23.2599, 77.4126),
    ('Indore', 'Indore', 'Madhya Pradesh', 'Commercial capital of MP', 22.7196, 75.8577),
    ('Gwalior', 'Gwalior', 'Madhya Pradesh', 'Historical city', 26.2183, 78.1828),
    ('Jabalpur', 'Jabalpur', 'Madhya Pradesh', 'Marble rocks city', 23.1815, 79.9864),
    # ── Bihar ──
    ('Patna', 'Patna', 'Bihar', 'Ancient Pataliputra', 25.5941, 85.1376),
    ('Gaya', 'Gaya', 'Bihar', 'Buddhist pilgrimage site', 24.7955, 85.0002),
    ('Muzaffarpur', 'Muzaffarpur', 'Bihar', 'Lychee city', 26.1209, 85.3647),
    # ── Odisha ──
    ('Bhubaneswar', 'Bhubaneswar', 'Odisha', 'Temple city', 20.2961, 85.8245),
    ('Cuttack', 'Cuttack', 'Odisha', 'Silver city', 20.4625, 85.8830),
    ('Rourkela', 'Rourkela', 'Odisha', 'Steel city', 22.2604, 84.8536),
    # ── Kerala ──
    ('Kochi', 'Kochi', 'Kerala', 'Queen of Arabian Sea', 9.9312, 76.2673),
    ('Thiruvananthapuram', 'Thiruvananthapuram', 'Kerala', 'State capital', 8.5241, 76.9366),
    ('Kozhikode', 'Kozhikode', 'Kerala', 'City of Spices', 11.2588, 75.7804),
    ('Thrissur', 'Thrissur', 'Kerala', 'Cultural capital of Kerala', 10.5276, 76.2144),
    # ── Punjab ──
    ('Ludhiana', 'Ludhiana', 'Punjab', 'Industrial hub', 30.9010, 75.8573),
    ('Amritsar', 'Amritsar', 'Punjab', 'Golden Temple city', 31.6340, 74.8723),
    ('Jalandhar', 'Jalandhar', 'Punjab', 'Sports goods hub', 31.3260, 75.5762),
    ('Chandigarh', 'Chandigarh', 'Chandigarh', 'Planned city', 30.7333, 76.7794),
    # ── Andhra Pradesh ──
    ('Visakhapatnam', 'Visakhapatnam', 'Andhra Pradesh', 'Port city', 17.6868, 83.2185),
    ('Vijayawada', 'Vijayawada', 'Andhra Pradesh', 'Business capital of AP', 16.5062, 80.6480),
    ('Guntur', 'Guntur', 'Andhra Pradesh', 'Chilli capital', 16.3067, 80.4365),
    ('Nellore', 'Nellore', 'Andhra Pradesh', 'Rice bowl of AP', 14.4426, 79.9865),
    # ── Jharkhand ──
    ('Ranchi', 'Ranchi', 'Jharkhand', 'City of waterfalls', 23.3441, 85.3096),
    ('Jamshedpur', 'Jamshedpur', 'Jharkhand', 'Steel city', 22.8046, 86.2029),
    ('Dhanbad', 'Dhanbad', 'Jharkhand', 'Coal capital', 23.7957, 86.4304),
    # ── Chhattisgarh ──
    ('Raipur', 'Raipur', 'Chhattisgarh', 'State capital', 21.2514, 81.6296),
    ('Bilaspur', 'Bilaspur', 'Chhattisgarh', 'Rice bowl of CG', 22.0797, 82.1391),
    # ── Assam ──
    ('Guwahati', 'Guwahati', 'Assam', 'Gateway to Northeast', 26.1445, 91.7362),
    ('Silchar', 'Silchar', 'Assam', 'Tea city', 24.8333, 92.7789),
    ('Dibrugarh', 'Dibrugarh', 'Assam', 'Tea capital', 27.4728, 94.9120),
    # ── Northeast ──
    ('Imphal', 'Imphal', 'Manipur', 'State capital', 24.8170, 93.9368),
    ('Shillong', 'Shillong', 'Meghalaya', 'Scotland of the East', 25.5788, 91.8933),
    ('Aizawl', 'Aizawl', 'Mizoram', 'State capital', 23.7271, 92.7176),
    ('Kohima', 'Kohima', 'Nagaland', 'State capital', 25.6751, 94.1086),
    ('Agartala', 'Agartala', 'Tripura', 'State capital', 23.8315, 91.2868),
    ('Itanagar', 'Itanagar', 'Arunachal Pradesh', 'State capital', 27.0844, 93.6053),
    # ── Himachal & Uttarakhand ──
    ('Shimla', 'Shimla', 'Himachal Pradesh', 'Summer capital', 31.1048, 77.1734),
    ('Dharamshala', 'Dharamshala', 'Himachal Pradesh', 'Tibetan hub', 32.2190, 76.3234),
    ('Dehradun', 'Dehradun', 'Uttarakhand', 'State capital', 30.3165, 78.0322),
    ('Haridwar', 'Haridwar', 'Uttarakhand', 'Holy city', 29.9457, 78.1642),
    # ── Goa ──
    ('Panaji', 'Panaji', 'Goa', 'State capital', 15.4909, 73.8278),
    # ── J&K & Ladakh ──
    ('Srinagar', 'Srinagar', 'Jammu & Kashmir', 'Paradise on Earth', 34.0837, 74.7973),
    ('Jammu', 'Jammu', 'Jammu & Kashmir', 'Winter capital', 32.7266, 74.8570),
    ('Leh', 'Leh', 'Ladakh', 'High altitude desert', 34.1526, 77.5771),
    # ── Union Territories ──
    ('Puducherry', 'Puducherry', 'Puducherry', 'French colonial town', 11.9416, 79.8083),
    ('Port Blair', 'Port Blair', 'Andaman & Nicobar', 'Island capital', 11.6234, 92.7265),
]
