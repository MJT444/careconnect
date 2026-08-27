const db = db.getSiblingDB("medical_db");

const pipeline = [
  {
    $facet: {
      ratingDistribution: [
        { $group: { _id: "$rating", count: { $sum: 1 } } },
        { $sort: { _id: 1 } },
        { $project: { _id: 0, rating: "$_id", count: 1 } },
      ],
      topTags: [
        { $unwind: "$tags" },
        { $group: { _id: "$tags", count: { $sum: 1 } } },
        { $sort: { count: -1 } },
        { $limit: 10 },
        { $project: { _id: 0, tag: "$_id", count: 1 } },
      ],
      overallAverage: [
        {
          $group: {
            _id: null,
            averageRating: { $avg: "$rating" },
            totalReviews: { $sum: 1 },
          },
        },
        {
          $project: {
            _id: 0,
            averageRating: { $round: ["$averageRating", 2] },
            totalReviews: 1,
          },
        },
      ],
    },
  },
];

const result = db.PatientReviews.aggregate(pipeline).toArray();

printjson(result);